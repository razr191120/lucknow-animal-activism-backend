import logging

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import CurrentUser, SessionDep
from app.models.user import User
from app.schemas.user import (
    OAuthFacebookBody,
    OAuthGoogleBody,
    OAuthInstagramBody,
    TokenResponse,
    UserCreate,
    UserCreateLaap,
    UserLogin,
    UserResponse,
)
from app.services.auth import create_access_token, hash_password, verify_password
from app.services.oauth_login import (
    exchange_instagram_code,
    verify_facebook_access_token,
    verify_google_id_token,
    verify_instagram_access_token,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(data: UserCreate, session: SessionDep) -> dict:
    try:
        result = await session.execute(
            select(User).where(User.email == data.email.lower())
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        try:
            password_hash = hash_password(data.password)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid password",
            ) from e

        user = User(
            email=data.email.lower(),
            full_name=data.full_name,
            hashed_password=password_hash,
            role="member",
        )
        session.add(user)
        await session.flush()
        await session.refresh(user)

        token = create_access_token(user.id, user.role)
        return {"access_token": token, "token_type": "bearer", "user": user}
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.exception("Database error during signup")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable",
        ) from e


@router.post(
    "/signup-laap", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
async def signup_laap(data: UserCreateLaap, session: SessionDep) -> dict:
    """LAAP: same `users` table as LWBP; requires Aadhaar and PAN."""
    try:
        result = await session.execute(
            select(User).where(User.email == data.email.lower())
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        r_aadhaar = await session.execute(
            select(User).where(User.aadhaar_number == data.aadhaar_number)
        )
        if r_aadhaar.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This Aadhaar number is already registered",
            )

        r_pan = await session.execute(
            select(User).where(User.pan_number == data.pan_number)
        )
        if r_pan.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This PAN is already registered",
            )

        try:
            password_hash = hash_password(data.password)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid password",
            ) from e

        user = User(
            email=data.email.lower(),
            full_name=data.full_name,
            hashed_password=password_hash,
            aadhaar_number=data.aadhaar_number,
            pan_number=data.pan_number,
            role="member",
        )
        session.add(user)
        await session.flush()
        await session.refresh(user)

        token = create_access_token(user.id, user.role)
        return {"access_token": token, "token_type": "bearer", "user": user}
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.exception("Database error during LAAP signup")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable",
        ) from e


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, session: SessionDep) -> dict:
    try:
        result = await session.execute(
            select(User).where(User.email == data.email.lower())
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        if user.hashed_password is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="This account uses social sign-in (Google, Facebook, or Instagram)",
            )
        if not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated",
            )

        token = create_access_token(user.id, user.role)
        return {"access_token": token, "token_type": "bearer", "user": user}
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.exception("Database error during login")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable",
        ) from e


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser) -> User:
    return current_user


async def _oauth_upsert_user(
    session: SessionDep,
    provider: str,
    sub: str,
    email: str,
    full_name: str,
) -> User:
    email_norm = email.lower().strip()
    r = await session.execute(
        select(User).where(User.oauth_provider == provider, User.oauth_sub == sub)
    )
    existing = r.scalar_one_or_none()
    if existing:
        if not existing.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated",
            )
        return existing

    r2 = await session.execute(select(User).where(User.email == email_norm))
    linked = r2.scalar_one_or_none()
    if linked:
        if not linked.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated",
            )
        linked.oauth_provider = provider
        linked.oauth_sub = sub
        await session.flush()
        await session.refresh(linked)
        return linked

    user = User(
        email=email_norm,
        full_name=full_name[:255],
        hashed_password=None,
        oauth_provider=provider,
        oauth_sub=sub,
        role="member",
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return user


@router.post("/oauth/google", response_model=TokenResponse)
async def oauth_google(
    body: OAuthGoogleBody,
    session: SessionDep,
) -> dict:
    claims = verify_google_id_token(body.id_token)
    user = await _oauth_upsert_user(
        session,
        claims["provider"],
        claims["sub"],
        claims["email"],
        claims["full_name"],
    )
    token = create_access_token(user.id, user.role)
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.post("/oauth/facebook", response_model=TokenResponse)
async def oauth_facebook(
    body: OAuthFacebookBody,
    session: SessionDep,
) -> dict:
    claims = await verify_facebook_access_token(body.access_token)
    user = await _oauth_upsert_user(
        session,
        claims["provider"],
        claims["sub"],
        claims["email"],
        claims["full_name"],
    )
    token = create_access_token(user.id, user.role)
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.post("/oauth/instagram", response_model=TokenResponse)
async def oauth_instagram(
    body: OAuthInstagramBody,
    session: SessionDep,
) -> dict:
    access = body.access_token
    if body.code:
        access = await exchange_instagram_code(body.code)
    assert access is not None
    claims = await verify_instagram_access_token(access)
    user = await _oauth_upsert_user(
        session,
        claims["provider"],
        claims["sub"],
        claims["email"],
        claims["full_name"],
    )
    token = create_access_token(user.id, user.role)
    return {"access_token": token, "token_type": "bearer", "user": user}
