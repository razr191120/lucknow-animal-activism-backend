import logging
import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import AdminUser, SessionDep
from app.models.attachment import Attachment
from app.models.distribution import Distribution
from app.models.drive import Drive
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserUpdate,
    UserUpdatePassword,
)
from app.services.auth import hash_password
from app.services.blob_storage import blob_storage_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


# ── Users ────────────────────────────────────────────────────────────────

@router.get("/users", response_model=list[UserResponse])
async def list_users(
    session: SessionDep,
    _admin: AdminUser,
    skip: int = 0,
    limit: int = 100,
) -> list[User]:
    result = await session.execute(
        select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    session: SessionDep,
    _admin: AdminUser,
) -> User:
    existing = await session.execute(
        select(User).where(User.email == data.email.lower())
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    try:
        password_hash = hash_password(data.password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid password",
        ) from e

    try:
        user = User(
            email=data.email.lower(),
            full_name=data.full_name,
            hashed_password=password_hash,
            role="member",
        )
        session.add(user)
        await session.flush()
        await session.refresh(user)
        return user
    except SQLAlchemyError:
        logger.exception("Database error creating user")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable",
        ) from None


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    session: SessionDep,
    _admin: AdminUser,
) -> User:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    session: SessionDep,
    _admin: AdminUser,
) -> User:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    update_fields = data.model_dump(exclude_unset=True)
    if "email" in update_fields and update_fields["email"]:
        update_fields["email"] = update_fields["email"].lower()
    for field, value in update_fields.items():
        setattr(user, field, value)

    await session.flush()
    await session.refresh(user)
    return user


@router.patch("/users/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_user_password(
    user_id: uuid.UUID,
    data: UserUpdatePassword,
    session: SessionDep,
    _admin: AdminUser,
) -> None:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        user.hashed_password = hash_password(data.new_password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid password",
        ) from e


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    session: SessionDep,
    admin: AdminUser,
) -> None:
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    await session.delete(user)


# ── Drives ───────────────────────────────────────────────────────────────

@router.patch("/drives/{drive_id}")
async def update_drive(
    drive_id: uuid.UUID,
    session: SessionDep,
    _admin: AdminUser,
    name: str | None = None,
    description: str | None = None,
    status_val: str | None = None,
) -> dict:
    result = await session.execute(select(Drive).where(Drive.id == drive_id))
    drive = result.scalar_one_or_none()
    if drive is None:
        raise HTTPException(status_code=404, detail="Drive not found")
    if name is not None:
        drive.name = name
    if description is not None:
        drive.description = description
    if status_val is not None:
        drive.status = status_val
    await session.flush()
    await session.refresh(drive)
    return {"id": str(drive.id), "name": drive.name, "status": drive.status}


@router.delete("/drives/{drive_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_drive(
    drive_id: uuid.UUID,
    session: SessionDep,
    _admin: AdminUser,
) -> None:
    result = await session.execute(select(Drive).where(Drive.id == drive_id))
    drive = result.scalar_one_or_none()
    if drive is None:
        raise HTTPException(status_code=404, detail="Drive not found")
    await session.delete(drive)


# ── Distributions ────────────────────────────────────────────────────────

@router.delete("/distributions/{dist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_distribution(
    dist_id: uuid.UUID,
    session: SessionDep,
    _admin: AdminUser,
) -> None:
    result = await session.execute(
        select(Distribution).where(Distribution.id == dist_id)
    )
    dist = result.scalar_one_or_none()
    if dist is None:
        raise HTTPException(status_code=404, detail="Distribution not found")

    attachments_result = await session.execute(
        select(Attachment).where(
            Attachment.entity_type == "distribution",
            Attachment.entity_id == dist_id,
        )
    )
    for att in attachments_result.scalars().all():
        blob_storage_service.delete(att.blob_name)
        await session.delete(att)

    await session.delete(dist)


# ── Attachments / Photos ─────────────────────────────────────────────────

@router.delete("/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_attachment(
    attachment_id: uuid.UUID,
    session: SessionDep,
    _admin: AdminUser,
) -> None:
    result = await session.execute(
        select(Attachment).where(Attachment.id == attachment_id)
    )
    attachment = result.scalar_one_or_none()
    if attachment is None:
        raise HTTPException(status_code=404, detail="Attachment not found")
    blob_storage_service.delete(attachment.blob_name)
    await session.delete(attachment)
