import datetime
import uuid

from pydantic import BaseModel, Field


class VolunteerCreate(BaseModel):
    phone: str | None = Field(None, max_length=20)
    skills: str | None = None
    availability: str | None = Field(None, max_length=100)
    area: str | None = Field(None, max_length=255)


class VolunteerUpdate(BaseModel):
    phone: str | None = Field(None, max_length=20)
    skills: str | None = None
    availability: str | None = Field(None, max_length=100)
    area: str | None = Field(None, max_length=255)
    status: str | None = Field(None, pattern="^(active|inactive)$")


class VolunteerResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    skills: str | None = None
    availability: str | None = None
    area: str | None = None
    status: str
    total_hours: float
    badge: str
    joined_at: datetime.datetime


class ActivityCreate(BaseModel):
    activity_type: str = Field(..., pattern="^(rescue|drive|general)$")
    entity_id: uuid.UUID | None = None
    description: str | None = None
    hours: float = Field(..., gt=0)
    date: datetime.date


class ActivityResponse(BaseModel):
    id: uuid.UUID
    volunteer_id: uuid.UUID
    activity_type: str
    entity_id: uuid.UUID | None = None
    description: str | None = None
    hours: float
    date: datetime.date
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class LeaderboardEntry(BaseModel):
    volunteer_id: uuid.UUID
    full_name: str
    total_hours: float
    badge: str
    area: str | None = None
