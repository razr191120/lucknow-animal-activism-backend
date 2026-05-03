"""laap platform tables: volunteers, donations, applications, assignments

Revision ID: c3f2a8d91e00
Revises: 7b9c1eae4f21
Create Date: 2026-05-04 02:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c3f2a8d91e00"
down_revision: Union[str, None] = "7b9c1eae4f21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "volunteers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("skills", sa.Text, nullable=True),
        sa.Column("availability", sa.String(100), nullable=True),
        sa.Column("area", sa.String(255), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("total_hours", sa.Float, nullable=False, server_default="0"),
        sa.Column("badge", sa.String(20), nullable=False, server_default="none"),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_volunteers_user_id", "volunteers", ["user_id"])

    op.create_table(
        "volunteer_activities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "volunteer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("volunteers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("activity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("hours", sa.Float, nullable=False, server_default="0"),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_volunteer_activities_volunteer_id",
        "volunteer_activities",
        ["volunteer_id"],
    )

    op.create_table(
        "donation_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("donor_name", sa.String(255), nullable=False),
        sa.Column("donor_email", sa.String(255), nullable=True),
        sa.Column("donor_phone", sa.String(20), nullable=True),
        sa.Column("amount_inr", sa.Numeric(12, 2), nullable=False),
        sa.Column("purpose", sa.String(500), nullable=True),
        sa.Column("payment_mode", sa.String(20), nullable=False, server_default="cash"),
        sa.Column("receipt_number", sa.String(50), nullable=False, unique=True),
        sa.Column(
            "campaign_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("laap_donation_requests.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "recorded_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_donation_records_receipt_number",
        "donation_records",
        ["receipt_number"],
    )

    op.create_table(
        "adoption_applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "adoption_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("laap_adoption_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "applicant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("applicant_name", sa.String(255), nullable=False),
        sa.Column("applicant_phone", sa.String(20), nullable=True),
        sa.Column("applicant_address", sa.Text, nullable=True),
        sa.Column("why_adopt", sa.Text, nullable=True),
        sa.Column("has_experience", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("living_situation", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("admin_notes", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_adoption_applications_adoption_id",
        "adoption_applications",
        ["adoption_id"],
    )
    op.create_index(
        "ix_adoption_applications_applicant_id",
        "adoption_applications",
        ["applicant_id"],
    )

    op.create_table(
        "rescue_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "rescue_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("laap_rescue_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "volunteer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("volunteers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "assigned_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="assigned"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_rescue_assignments_rescue_id",
        "rescue_assignments",
        ["rescue_id"],
    )
    op.create_index(
        "ix_rescue_assignments_volunteer_id",
        "rescue_assignments",
        ["volunteer_id"],
    )


def downgrade() -> None:
    op.drop_table("rescue_assignments")
    op.drop_table("adoption_applications")
    op.drop_table("donation_records")
    op.drop_table("volunteer_activities")
    op.drop_table("volunteers")
