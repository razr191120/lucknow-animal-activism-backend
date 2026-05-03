"""laap requests and user kyc

Revision ID: 7b9c1eae4f21
Revises: a2e5b57fe8f6
Create Date: 2026-05-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7b9c1eae4f21"
down_revision: Union[str, None] = "a2e5b57fe8f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("aadhaar_number", sa.String(length=12), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("pan_number", sa.String(length=10), nullable=True),
    )
    op.create_index(
        "ix_users_aadhaar_number",
        "users",
        ["aadhaar_number"],
        unique=True,
    )
    op.create_index(
        "ix_users_pan_number",
        "users",
        ["pan_number"],
        unique=True,
    )

    op.create_table(
        "laap_adoption_requests",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("animal_name", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("contact_phone", sa.String(length=20), nullable=True),
        sa.Column("location_hint", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_laap_adoption_requests_user_id"),
        "laap_adoption_requests",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "laap_rescue_requests",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("location_address", sa.Text(), nullable=False),
        sa.Column("contact_phone", sa.String(length=20), nullable=True),
        sa.Column("animal_condition", sa.String(length=255), nullable=True),
        sa.Column("urgency", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_laap_rescue_requests_user_id"),
        "laap_rescue_requests",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "laap_donation_requests",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("items_or_need_summary", sa.Text(), nullable=True),
        sa.Column("how_to_donate", sa.Text(), nullable=True),
        sa.Column("contact_phone", sa.String(length=20), nullable=True),
        sa.Column("upi_id", sa.String(length=100), nullable=True),
        sa.Column("bank_account_hint", sa.Text(), nullable=True),
        sa.Column("target_amount_inr", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_laap_donation_requests_user_id"),
        "laap_donation_requests",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_laap_donation_requests_user_id"), table_name="laap_donation_requests"
    )
    op.drop_table("laap_donation_requests")
    op.drop_index(
        op.f("ix_laap_rescue_requests_user_id"), table_name="laap_rescue_requests"
    )
    op.drop_table("laap_rescue_requests")
    op.drop_index(
        op.f("ix_laap_adoption_requests_user_id"), table_name="laap_adoption_requests"
    )
    op.drop_table("laap_adoption_requests")
    op.drop_index("ix_users_pan_number", table_name="users")
    op.drop_index("ix_users_aadhaar_number", table_name="users")
    op.drop_column("users", "pan_number")
    op.drop_column("users", "aadhaar_number")
