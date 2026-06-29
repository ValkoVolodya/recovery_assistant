from dataclasses import dataclass
from decimal import Decimal
import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import Workout, User
from app.dto.recovery import RecoveryRecommendation
from app.dto.workout import WorkoutInput
from app.repositories.users import UserRepository
from app.repositories.workouts import WorkoutRepository
from app.services.recommendations import RecoveryRecommendationService
from app.services.telegram import TelegramNotificationService

logger = logging.getLogger(__name__)


@dataclass
class ServiceResult:
    user: User
    workout: Workout | None = None
    recommendation: RecoveryRecommendation | None = None


class ProfileService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def ensure_user(self, telegram_user_id: int, username: str | None, first_name: str) -> User:
        async with self._session_factory() as session:
            repo = UserRepository(session)
            user = await repo.create_or_update_identity(telegram_user_id, username, first_name)
            await session.commit()
            return user

    async def get_profile(self, telegram_user_id: int) -> User | None:
        async with self._session_factory() as session:
            return await UserRepository(session).get_by_telegram_user_id(telegram_user_id)

    async def set_weight(
        self,
        telegram_user_id: int,
        username: str | None,
        first_name: str,
        weight_kg: float,
    ) -> User:
        async with self._session_factory() as session:
            repo = UserRepository(session)
            user = await repo.create_or_update_identity(telegram_user_id, username, first_name)
            await repo.update_weight(user, weight_kg)
            await session.commit()
            return user

class WorkoutService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        recommendation_service: RecoveryRecommendationService,
        telegram_notification_service: TelegramNotificationService | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._recommendation_service = recommendation_service
        self._telegram_notification_service = telegram_notification_service

    async def log_workout(
        self,
        telegram_user_id: int,
        username: str | None,
        first_name: str,
        workout_input: WorkoutInput,
        provider_activity_id: int | None = None,
    ) -> ServiceResult:
        async with self._session_factory() as session:
            user_repo = UserRepository(session)
            workout_repo = WorkoutRepository(session)

            user = await user_repo.create_or_update_identity(telegram_user_id, username, first_name)
            recommendation = self._recommendation_service.recommend(
                workout=workout_input,
                weight_kg=self._to_float(user.weight_kg),
            )
            workout = Workout(
                user_id=user.id,
                provider_activity_id=provider_activity_id,
                duration_minutes=workout_input.duration_minutes,
                kilojoules=workout_input.kilojoules,
                intensity=workout_input.intensity,
                carbs_min=recommendation.carbs_min_g,
                carbs_max=recommendation.carbs_max_g,
                protein_min=recommendation.protein_min_g,
                protein_max=recommendation.protein_max_g,
                fluids_ml_min=recommendation.fluids_ml_min,
                fluids_ml_max=recommendation.fluids_ml_max,
                sodium_mg_min=recommendation.sodium_mg_min,
                sodium_mg_max=recommendation.sodium_mg_max,
                explanation=recommendation.explanation,
            )
            await workout_repo.add(workout)
            await session.commit()
            if self._telegram_notification_service is not None:
                await self._notify_recommendation(
                    telegram_user_id=telegram_user_id,
                    workout=workout,
                    recommendation=recommendation,
                )
            return ServiceResult(user=user, workout=workout, recommendation=recommendation)

    async def get_last_workout(self, telegram_user_id: int) -> ServiceResult | None:
        async with self._session_factory() as session:
            user_repo = UserRepository(session)
            workout_repo = WorkoutRepository(session)
            user = await user_repo.get_by_telegram_user_id(telegram_user_id)
            if user is None:
                return None
            workout = await workout_repo.get_last_for_user(user.id)
            if workout is None:
                return ServiceResult(user=user)
            recommendation = RecoveryRecommendation(**workout.recommendation_payload())
            return ServiceResult(user=user, workout=workout, recommendation=recommendation)

    def _to_float(self, value: Decimal | float | None) -> float | None:
        if value is None:
            return None
        return float(value)

    async def _notify_recommendation(
        self,
        telegram_user_id: int,
        workout: Workout,
        recommendation: RecoveryRecommendation,
    ) -> None:
        try:
            await self._telegram_notification_service.send_workout_recommendation(
                telegram_user_id=telegram_user_id,
                workout=workout,
                recommendation=recommendation,
            )
        except Exception:
            logger.exception(
                "Workout was stored but recommendation delivery failed for telegram_user_id=%s",
                telegram_user_id,
            )
