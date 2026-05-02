import datetime
import uuid

from pydantic import BaseModel, Field


class DriveAddressBase(BaseModel):
    address: str = Field(..., min_length=1, max_length=1000)


class DriveAddressCreate(DriveAddressBase):
    pass


class DriveAddressResponse(DriveAddressBase):
    id: uuid.UUID
    drive_id: uuid.UUID
    latitude: float | None = None
    longitude: float | None = None
    order_index: int | None = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class DriveCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    planned_date: datetime.date


class DriveResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    planned_date: datetime.date
    status: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    addresses: list[DriveAddressResponse] = []

    model_config = {"from_attributes": True}


class DriveListResponse(BaseModel):
    id: uuid.UUID
    name: str
    planned_date: datetime.date
    status: str
    address_count: int = 0
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class AddAddressesRequest(BaseModel):
    addresses: list[str] = Field(..., min_length=1)
