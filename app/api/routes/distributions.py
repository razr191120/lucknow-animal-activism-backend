import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select

from app.api.deps import SessionDep
from app.models.attachment import Attachment
from app.models.distribution import Distribution
from app.schemas.distribution import DistributionResponse
from app.services.blob_storage import blob_storage_service

router = APIRouter(prefix="/distributions", tags=["distributions"])


async def _upload_and_track(
    upload: UploadFile,
    session: SessionDep,
    entity_type: str,
    entity_id: uuid.UUID,
    field_name: str,
) -> str:
    blob_name, blob_url, size_bytes = await blob_storage_service.upload(upload)

    attachment = Attachment(
        blob_name=blob_name,
        blob_url=blob_url,
        original_filename=upload.filename,
        content_type=upload.content_type,
        size_bytes=size_bytes,
        entity_type=entity_type,
        entity_id=entity_id,
        field_name=field_name,
    )
    session.add(attachment)
    return blob_url


@router.post("/", response_model=DistributionResponse, status_code=status.HTTP_201_CREATED)
async def create_distribution(
    session: SessionDep,
    name: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    contact: str | None = Form(None),
    description: str | None = Form(None),
    address: str | None = Form(None),
    drive_id: uuid.UUID | None = Form(None),
    water_bowl_photo: UploadFile | None = File(None),
    owner_photo: UploadFile | None = File(None),
) -> Distribution:
    dist = Distribution(
        drive_id=drive_id,
        name=name,
        contact=contact,
        description=description,
        address=address,
        latitude=latitude,
        longitude=longitude,
    )
    session.add(dist)
    await session.flush()
    await session.refresh(dist)

    if water_bowl_photo and water_bowl_photo.filename:
        dist.water_bowl_photo = await _upload_and_track(
            water_bowl_photo, session, "distribution", dist.id, "water_bowl_photo"
        )

    if owner_photo and owner_photo.filename:
        dist.owner_photo = await _upload_and_track(
            owner_photo, session, "distribution", dist.id, "owner_photo"
        )

    await session.flush()
    await session.refresh(dist)
    return dist


@router.get("/", response_model=list[DistributionResponse])
async def list_distributions(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
) -> list[Distribution]:
    result = await session.execute(
        select(Distribution)
        .order_by(Distribution.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


@router.get("/{distribution_id}", response_model=DistributionResponse)
async def get_distribution(
    distribution_id: uuid.UUID,
    session: SessionDep,
) -> Distribution:
    result = await session.execute(
        select(Distribution).where(Distribution.id == distribution_id)
    )
    dist = result.scalar_one_or_none()
    if dist is None:
        raise HTTPException(status_code=404, detail="Distribution not found")
    return dist
