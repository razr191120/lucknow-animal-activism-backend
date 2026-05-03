import datetime
import uuid

from pydantic import BaseModel, Field


class ApplicationCreate(BaseModel):
    applicant_name: str = Field(..., min_length=1, max_length=255)
    applicant_phone: str | None = Field(None, max_length=20)
    applicant_address: str | None = None
    why_adopt: str | None = None
    has_experience: bool = False
    living_situation: str | None = None


class ApplicationUpdate(BaseModel):
    status: str | None = Field(None, pattern="^(pending|approved|rejected)$")
    admin_notes: str | None = None


class ApplicationResponse(BaseModel):
    id: uuid.UUID
    adoption_id: uuid.UUID
    applicant_id: uuid.UUID
    applicant_name: str
    applicant_phone: str | None = None
    applicant_address: str | None = None
    why_adopt: str | None = None
    has_experience: bool
    living_situation: str | None = None
    status: str
    admin_notes: str | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}
