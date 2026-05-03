import logging

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import CurrentUser, SessionDep
from app.models.user import User
from app.schemas.user import (
    TokenResponse,
    UserCreate,
    UserCreateLaap,
    UserLogin,
    UserResponse,
)
from app.services.auth import create_access_token, hash_password, verify_password

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
        if user is None or not verify_password(data.password, user.hashed_password):
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
