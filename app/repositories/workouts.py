from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Workout


class WorkoutRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, workout: Workout) -> Workout:
        self._session.add(workout)
        await self._session.flush()
        return workout

    async def get_last_for_user(self, user_id: int) -> Workout | None:
        stmt = (
            select(Workout)
            .where(Workout.user_id == user_id)
            .order_by(Workout.created_at.desc(), Workout.id.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_provider_activity_id(self, provider_activity_id: int) -> Workout | None:
        stmt = select(Workout).where(Workout.provider_activity_id == provider_activity_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
