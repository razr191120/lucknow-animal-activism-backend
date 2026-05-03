import datetime
import uuid
from decimal import Decimal

from pydantic import BaseModel, Field


class LaapAdoptionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    creator_full_name: str | None = None
    title: str
    animal_name: str | None
    description: str | None
    contact_phone: str | None
    location_hint: str | None
    status: str
    photo_urls: list[str] = Field(default_factory=list)
    created_at: datetime.datetime
    updated_at: datetime.datetime


class LaapAdoptionUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    animal_name: str | None = Field(None, max_length=255)
    description: str | None = None
    contact_phone: str | None = Field(None, max_length=20)
    location_hint: str | None = None
    status: str | None = Field(None, pattern="^(open|fulfilled|withdrawn)$")


class LaapRescueResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    creator_full_name: str | None = None
    title: str
    description: str | None
    location_address: str
    contact_phone: str | None
    animal_condition: str | None
    urgency: str
    status: str
    photo_urls: list[str] = Field(default_factory=list)
    created_at: datetime.datetime
    updated_at: datetime.datetime


class LaapRescueUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    location_address: str | None = None
    contact_phone: str | None = Field(None, max_length=20)
    animal_condition: str | None = Field(None, max_length=255)
    urgency: str | None = Field(None, pattern="^(urgent|high|medium)$")
    status: str | None = Field(None, pattern="^(open|resolved|withdrawn)$")


class LaapDonationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    creator_full_name: str | None = None
    title: str
    description: str | None
    items_or_need_summary: str | None
    how_to_donate: str | None
    contact_phone: str | None
    upi_id: str | None
    bank_account_hint: str | None
    target_amount_inr: Decimal | None
    status: str
    photo_urls: list[str] = Field(default_factory=list)
    created_at: datetime.datetime
    updated_at: datetime.datetime


class LaapDonationUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    items_or_need_summary: str | None = None
    how_to_donate: str | None = None
    contact_phone: str | None = Field(None, max_length=20)
    upi_id: str | None = Field(None, max_length=100)
    bank_account_hint: str | None = None
    target_amount_inr: Decimal | None = None
    status: str | None = Field(None, pattern="^(open|fulfilled|withdrawn)$")
