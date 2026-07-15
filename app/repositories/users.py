from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_telegram_user_id(self, telegram_user_id: int) -> User | None:
        stmt = select(User).where(User.telegram_user_id == telegram_user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_or_update_identity(
        self,
        telegram_user_id: int,
        username: str | None,
        first_name: str,
    ) -> User:
        user = await self.get_by_telegram_user_id(telegram_user_id)
        if user is None:
            user = User(
                telegram_user_id=telegram_user_id,
                username=username,
                first_name=first_name,
            )
            self._session.add(user)
        else:
            user.username = username
            user.first_name = first_name
        await self._session.flush()
        return user

    async def update_weight(self, user: User, weight_kg: float) -> User:
        user.weight_kg = weight_kg
        await self._session.flush()
        return user

    async def update_ftp(self, user: User, ftp_watts: int) -> User:
        user.ftp_watts = ftp_watts
        await self._session.flush()
        return user
