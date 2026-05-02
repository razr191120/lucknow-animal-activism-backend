import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select

from app.api.deps import SessionDep
from app.config import settings
from app.models.distribution import Distribution
from app.schemas.distribution import DistributionResponse

router = APIRouter(prefix="/distributions", tags=["distributions"])


async def _save_upload(upload: UploadFile) -> str:
    ext = upload.filename.rsplit(".", 1)[-1] if upload.filename and "." in upload.filename else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"
    dest = settings.upload_path / filename
    content = await upload.read()
    dest.write_bytes(content)
    return f"/uploads/{filename}"


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
    water_bowl_path: str | None = None
    owner_photo_path: str | None = None

    if water_bowl_photo and water_bowl_photo.filename:
        water_bowl_path = await _save_upload(water_bowl_photo)
    if owner_photo and owner_photo.filename:
        owner_photo_path = await _save_upload(owner_photo)

    dist = Distribution(
        drive_id=drive_id,
        name=name,
        contact=contact,
        description=description,
        address=address,
        latitude=latitude,
        longitude=longitude,
        water_bowl_photo=water_bowl_path,
        owner_photo=owner_photo_path,
    )
    session.add(dist)
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
