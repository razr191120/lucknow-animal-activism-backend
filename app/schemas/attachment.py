import datetime
import uuid

from pydantic import BaseModel


class AttachmentResponse(BaseModel):
    id: uuid.UUID
    blob_name: str
    blob_url: str
    original_filename: str | None = None
    content_type: str | None = None
    size_bytes: int | None = None
    entity_type: str
    entity_id: uuid.UUID | None = None
    field_name: str | None = None
    uploaded_by: str | None = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}
