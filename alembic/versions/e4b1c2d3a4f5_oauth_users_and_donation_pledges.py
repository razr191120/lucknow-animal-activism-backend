"""oauth users and donation pledges

Revision ID: e4b1c2d3a4f5
Revises: c3f2a8d91e00
Create Date: 2026-05-04 03:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "e4b1c2d3a4f5"
down_revision: Union[str, None] = "c3f2a8d91e00"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "hashed_password",
        existing_type=sa.String(length=500),
        nullable=True,
    )
    op.add_column(
        "users",
        sa.Column("oauth_provider", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("oauth_sub", sa.String(length=255), nullable=True),
    )
    op.create_index("ix_users_oauth_provider", "users", ["oauth_provider"])
    op.execute(
        """
        CREATE UNIQUE INDEX uq_users_oauth_provider_sub
        ON users (oauth_provider, oauth_sub)
        WHERE oauth_provider IS NOT NULL AND oauth_sub IS NOT NULL
        """
    )

    op.create_table(
        "donation_pledges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "donation_request_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("laap_donation_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("amount_inr", sa.Numeric(12, 2), nullable=True),
        sa.Column("message", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_donation_pledges_donation_request_id",
        "donation_pledges",
        ["donation_request_id"],
    )
    op.create_index(
        "ix_donation_pledges_user_id",
        "donation_pledges",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_table("donation_pledges")
    op.execute("DROP INDEX IF EXISTS uq_users_oauth_provider_sub")
    op.drop_index("ix_users_oauth_provider", table_name="users")
    op.drop_column("users", "oauth_sub")
    op.drop_column("users", "oauth_provider")
    op.alter_column(
        "users",
        "hashed_password",
        existing_type=sa.String(length=500),
        nullable=False,
    )
