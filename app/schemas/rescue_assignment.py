import datetime
import uuid

from pydantic import BaseModel, Field


class AssignmentCreate(BaseModel):
    volunteer_id: uuid.UUID
    notes: str | None = None


class AssignmentUpdate(BaseModel):
    status: str | None = Field(
        None, pattern="^(assigned|en_route|on_scene|completed)$"
    )
    notes: str | None = None


class AssignmentResponse(BaseModel):
    id: uuid.UUID
    rescue_id: uuid.UUID
    volunteer_id: uuid.UUID
    volunteer_name: str | None = None
    assigned_by: uuid.UUID
    status: str
    notes: str | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
