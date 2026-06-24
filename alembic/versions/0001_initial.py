"""initial schema

Revision ID: 0001_initial
Revises: 
Create Date: 2026-04-23 00:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


goal_enum = postgresql.ENUM(
    "performance",
    "maintenance",
    "fat_loss",
    name="goal_enum",
    create_type=False,
)
intensity_enum = postgresql.ENUM(
    "easy",
    "moderate",
    "hard",
    name="intensity_enum",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    goal_enum.create(bind, checkfirst=True)
    intensity_enum.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_user_id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=255), nullable=False),
        sa.Column("weight_kg", sa.Numeric(5, 2), nullable=True),
        sa.Column("goal", goal_enum, nullable=False, server_default="maintenance"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("telegram_user_id"),
    )
    op.create_index("ix_users_telegram_user_id", "users", ["telegram_user_id"], unique=False)

    op.create_table(
        "workouts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("kilojoules", sa.Integer(), nullable=False),
        sa.Column("intensity", intensity_enum, nullable=False),
        sa.Column("carbs_min", sa.Integer(), nullable=False),
        sa.Column("carbs_max", sa.Integer(), nullable=False),
        sa.Column("protein_min", sa.Integer(), nullable=False),
        sa.Column("protein_max", sa.Integer(), nullable=False),
        sa.Column("fluids_ml_min", sa.Integer(), nullable=False),
        sa.Column("fluids_ml_max", sa.Integer(), nullable=False),
        sa.Column("sodium_mg_min", sa.Integer(), nullable=False),
        sa.Column("sodium_mg_max", sa.Integer(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_workouts_user_id", "workouts", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_workouts_user_id", table_name="workouts")
    op.drop_table("workouts")
    op.drop_index("ix_users_telegram_user_id", table_name="users")
    op.drop_table("users")

    bind = op.get_bind()
    intensity_enum.drop(bind, checkfirst=True)
    goal_enum.drop(bind, checkfirst=True)
