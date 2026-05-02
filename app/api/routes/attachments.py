import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import SessionDep
from app.models.attachment import Attachment
from app.schemas.attachment import AttachmentResponse
from app.services.blob_storage import blob_storage_service

router = APIRouter(prefix="/attachments", tags=["attachments"])


@router.get("/", response_model=list[AttachmentResponse])
async def list_attachments(
    session: SessionDep,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Attachment]:
    query = select(Attachment).order_by(Attachment.created_at.desc())
    if entity_type:
        query = query.where(Attachment.entity_type == entity_type)
    if entity_id:
        query = query.where(Attachment.entity_id == entity_id)
    result = await session.execute(query.offset(skip).limit(limit))
    return list(result.scalars().all())


@router.get("/{attachment_id}", response_model=AttachmentResponse)
async def get_attachment(
    attachment_id: uuid.UUID,
    session: SessionDep,
) -> Attachment:
    result = await session.execute(
        select(Attachment).where(Attachment.id == attachment_id)
    )
    attachment = result.scalar_one_or_none()
    if attachment is None:
        raise HTTPException(status_code=404, detail="Attachment not found")
    return attachment


@router.delete("/{attachment_id}", status_code=204)
async def delete_attachment(
    attachment_id: uuid.UUID,
    session: SessionDep,
) -> None:
    result = await session.execute(
        select(Attachment).where(Attachment.id == attachment_id)
    )
    attachment = result.scalar_one_or_none()
    if attachment is None:
        raise HTTPException(status_code=404, detail="Attachment not found")

    blob_storage_service.delete(attachment.blob_name)
    await session.delete(attachment)
