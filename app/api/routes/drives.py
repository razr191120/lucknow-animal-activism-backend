import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import SessionDep
from app.models.drive import Drive, DriveAddress
from app.schemas.drive import (
    AddAddressesRequest,
    DriveAddressResponse,
    DriveCreate,
    DriveListResponse,
    DriveResponse,
)
from app.services.geocoding import geocoding_service

router = APIRouter(prefix="/drives", tags=["drives"])


@router.post("/", response_model=DriveResponse, status_code=status.HTTP_201_CREATED)
async def create_drive(data: DriveCreate, session: SessionDep) -> Drive:
    drive = Drive(
        name=data.name,
        description=data.description,
        planned_date=data.planned_date,
    )
    session.add(drive)
    await session.flush()
    await session.refresh(drive, attribute_names=["addresses"])
    return drive


@router.get("/", response_model=list[DriveListResponse])
async def list_drives(session: SessionDep) -> list[dict]:
    result = await session.execute(
        select(Drive).options(selectinload(Drive.addresses)).order_by(Drive.planned_date.desc())
    )
    drives = result.scalars().all()
    return [
        {
            "id": d.id,
            "name": d.name,
            "planned_date": d.planned_date,
            "status": d.status,
            "address_count": len(d.addresses),
            "created_at": d.created_at,
        }
        for d in drives
    ]


@router.get("/{drive_id}", response_model=DriveResponse)
async def get_drive(drive_id: uuid.UUID, session: SessionDep) -> Drive:
    result = await session.execute(
        select(Drive)
        .options(selectinload(Drive.addresses))
        .where(Drive.id == drive_id)
    )
    drive = result.scalar_one_or_none()
    if drive is None:
        raise HTTPException(status_code=404, detail="Drive not found")
    return drive


@router.post(
    "/{drive_id}/addresses",
    response_model=list[DriveAddressResponse],
    status_code=status.HTTP_201_CREATED,
)
async def add_addresses(
    drive_id: uuid.UUID,
    data: AddAddressesRequest,
    session: SessionDep,
) -> list[DriveAddress]:
    result = await session.execute(select(Drive).where(Drive.id == drive_id))
    drive = result.scalar_one_or_none()
    if drive is None:
        raise HTTPException(status_code=404, detail="Drive not found")

    geocoded = await geocoding_service.geocode_batch(data.addresses)

    new_addresses: list[DriveAddress] = []
    for i, geo in enumerate(geocoded):
        addr = DriveAddress(
            drive_id=drive_id,
            address=geo.address,
            latitude=geo.latitude,
            longitude=geo.longitude,
            order_index=i,
        )
        session.add(addr)
        new_addresses.append(addr)

    await session.flush()
    for addr in new_addresses:
        await session.refresh(addr)

    return new_addresses
