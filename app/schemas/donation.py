import datetime
import uuid
from decimal import Decimal

from pydantic import BaseModel, Field


class DonationCreate(BaseModel):
    donor_name: str = Field(..., min_length=1, max_length=255)
    donor_email: str | None = Field(None, max_length=255)
    donor_phone: str | None = Field(None, max_length=20)
    amount_inr: Decimal = Field(..., gt=0)
    purpose: str | None = Field(None, max_length=500)
    payment_mode: str = Field("cash", pattern="^(cash|upi|bank|other)$")
    campaign_id: uuid.UUID | None = None
    date: datetime.date
    notes: str | None = None


class DonationResponse(BaseModel):
    id: uuid.UUID
    donor_name: str
    donor_email: str | None = None
    donor_phone: str | None = None
    amount_inr: Decimal
    purpose: str | None = None
    payment_mode: str
    receipt_number: str
    campaign_id: uuid.UUID | None = None
    recorded_by: uuid.UUID
    date: datetime.date
    notes: str | None = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class DonationStatsResponse(BaseModel):
    total_amount_inr: Decimal
    donation_count: int
