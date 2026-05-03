import datetime
import uuid
from decimal import Decimal

from sqlalchemy import DateTime, Date, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DonationRecord(Base):
    __tablename__ = "donation_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    donor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    donor_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    donor_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    amount_inr: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    purpose: Mapped[str | None] = mapped_column(String(500), nullable=True)
    payment_mode: Mapped[str] = mapped_column(
        String(20), nullable=False, default="cash"
    )
    receipt_number: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("laap_donation_requests.id", ondelete="SET NULL"),
        nullable=True,
    )
    recorded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
