from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.enums import Goal, Intensity


def enum_values(enum_class: type[Goal] | type[Intensity]) -> list[str]:
    return [member.value for member in enum_class]


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_user_id: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    weight_kg: Mapped[float | None] = mapped_column(Numeric(5, 2))
    ftp_watts: Mapped[int | None] = mapped_column(Integer)
    goal: Mapped[Goal] = mapped_column(
        Enum(Goal, name="goal_enum", values_callable=enum_values),
        default=Goal.MAINTENANCE,
        nullable=False,
    )

    workouts: Mapped[list["Workout"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    strava_connection: Mapped["StravaConnection | None"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )


class Workout(Base):
    __tablename__ = "workouts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_activity_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    kilojoules: Mapped[int] = mapped_column(Integer, nullable=False)
    intensity: Mapped[Intensity] = mapped_column(
        Enum(Intensity, name="intensity_enum", values_callable=enum_values),
        nullable=False,
    )
    carbs_min: Mapped[int] = mapped_column(Integer, nullable=False)
    carbs_max: Mapped[int] = mapped_column(Integer, nullable=False)
    protein_min: Mapped[int] = mapped_column(Integer, nullable=False)
    protein_max: Mapped[int] = mapped_column(Integer, nullable=False)
    fluids_ml_min: Mapped[int] = mapped_column(Integer, nullable=False)
    fluids_ml_max: Mapped[int] = mapped_column(Integer, nullable=False)
    sodium_mg_min: Mapped[int] = mapped_column(Integer, nullable=False)
    sodium_mg_max: Mapped[int] = mapped_column(Integer, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="workouts")

    def recommendation_payload(self) -> dict[str, Any]:
        return {
            "carbs_min_g": self.carbs_min,
            "carbs_max_g": self.carbs_max,
            "protein_min_g": self.protein_min,
            "protein_max_g": self.protein_max,
            "fluids_ml_min": self.fluids_ml_min,
            "fluids_ml_max": self.fluids_ml_max,
            "sodium_mg_min": self.sodium_mg_min,
            "sodium_mg_max": self.sodium_mg_max,
            "explanation": self.explanation,
        }


class StravaConnection(Base, TimestampMixin):
    __tablename__ = "strava_connections"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    strava_athlete_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship(back_populates="strava_connection")
