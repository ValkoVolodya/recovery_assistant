from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.config import Settings, get_settings
from app.db.session import create_engine, create_session_factory
from app.services.app_services import ProfileService, WorkoutService
from app.services.recommendations import RecoveryRecommendationService
from app.services.strava import StravaService


@dataclass
class AppRuntime:
    settings: Settings
    engine: AsyncEngine
    session_factory: async_sessionmaker[AsyncSession]
    profile_service: ProfileService
    workout_service: WorkoutService
    strava_service: StravaService


def build_runtime() -> AppRuntime:
    settings = get_settings()
    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    recommendation_service = RecoveryRecommendationService()
    profile_service = ProfileService(session_factory)
    workout_service = WorkoutService(session_factory, recommendation_service)
    strava_service = StravaService(settings, session_factory, workout_service)
    return AppRuntime(
        settings=settings,
        engine=engine,
        session_factory=session_factory,
        profile_service=profile_service,
        workout_service=workout_service,
        strava_service=strava_service,
    )
