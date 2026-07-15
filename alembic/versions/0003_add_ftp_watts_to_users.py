"""add ftp watts to users

Revision ID: 0003_add_ftp_watts_to_users
Revises: 0002_strava_integration
Create Date: 2026-07-15 00:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0003_add_ftp_watts_to_users"
down_revision: str | None = "0002_strava_integration"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("ftp_watts", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "ftp_watts")
