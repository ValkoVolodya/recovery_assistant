from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import StravaConnection


class StravaConnectionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_id(self, user_id: int) -> StravaConnection | None:
        stmt = select(StravaConnection).where(StravaConnection.user_id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_athlete_id(self, athlete_id: int) -> StravaConnection | None:
        stmt = select(StravaConnection).where(StravaConnection.strava_athlete_id == athlete_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_connection(
        self,
        user_id: int,
        athlete_id: int,
        access_token: str,
        refresh_token: str,
        expires_at: datetime,
    ) -> StravaConnection:
        connection = await self.get_by_user_id(user_id)
        if connection is None:
            connection = StravaConnection(
                user_id=user_id,
                strava_athlete_id=athlete_id,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
            )
            self._session.add(connection)
        else:
            connection.strava_athlete_id = athlete_id
            connection.access_token = access_token
            connection.refresh_token = refresh_token
            connection.expires_at = expires_at
        await self._session.flush()
        return connection
