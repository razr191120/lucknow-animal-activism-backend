import datetime
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AdoptionApplication(Base):
    __tablename__ = "adoption_applications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    adoption_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("laap_adoption_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    applicant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    applicant_name: Mapped[str] = mapped_column(String(255), nullable=False)
    applicant_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    applicant_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    why_adopt: Mapped[str | None] = mapped_column(Text, nullable=True)
    has_experience: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    living_situation: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
