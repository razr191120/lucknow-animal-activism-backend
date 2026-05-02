import datetime
import uuid

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    blob_name: Mapped[str] = mapped_column(
        String(500), nullable=False, unique=True
    )
    blob_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    original_filename: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    content_type: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    entity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    field_name: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    uploaded_by: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
