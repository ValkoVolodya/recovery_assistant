"""add strava integration tables

Revision ID: 0002_strava_integration
Revises: 0001_initial
Create Date: 2026-06-24 00:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0002_strava_integration"
down_revision: str | None = "0001_initial"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "strava_connections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("strava_athlete_id", sa.BigInteger(), nullable=False),
        sa.Column("access_token", sa.Text(), nullable=False),
        sa.Column("refresh_token", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id"),
        sa.UniqueConstraint("strava_athlete_id"),
    )
    op.create_index(
        "ix_strava_connections_strava_athlete_id",
        "strava_connections",
        ["strava_athlete_id"],
        unique=False,
    )

    op.add_column("workouts", sa.Column("provider_activity_id", sa.BigInteger(), nullable=True))
    op.create_unique_constraint(
        "uq_workouts_provider_activity_id",
        "workouts",
        ["provider_activity_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_workouts_provider_activity_id", "workouts", type_="unique")
    op.drop_column("workouts", "provider_activity_id")

    op.drop_index("ix_strava_connections_strava_athlete_id", table_name="strava_connections")
    op.drop_table("strava_connections")
