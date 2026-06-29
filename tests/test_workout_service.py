import importlib
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from types import SimpleNamespace


def _load_app_services():
    sys.modules.pop("app.services.app_services", None)

    class FakeAsyncSessionMaker:
        def __class_getitem__(cls, item):
            return cls

    sys.modules["sqlalchemy.ext.asyncio"] = types.SimpleNamespace(
        AsyncSession=object,
        async_sessionmaker=FakeAsyncSessionMaker,
    )

    class FakeUser:
        def __init__(self, id: int, weight_kg: float | None) -> None:
            self.id = id
            self.weight_kg = weight_kg

    class FakeWorkout:
        def __init__(self, **kwargs) -> None:
            self.__dict__.update(kwargs)

    sys.modules["app.db.models"] = types.SimpleNamespace(User=FakeUser, Workout=FakeWorkout)
    sys.modules["app.dto.recovery"] = types.SimpleNamespace(RecoveryRecommendation=object)
    sys.modules["app.dto.workout"] = types.SimpleNamespace(WorkoutInput=object)
    sys.modules["app.repositories.users"] = types.SimpleNamespace(UserRepository=object)
    sys.modules["app.repositories.workouts"] = types.SimpleNamespace(WorkoutRepository=object)
    sys.modules["app.services.recommendations"] = types.SimpleNamespace(RecoveryRecommendationService=object)
    sys.modules["app.services.telegram"] = types.SimpleNamespace(TelegramNotificationService=object)
    module_path = Path(__file__).resolve().parents[1] / "app" / "services" / "app_services.py"
    spec = importlib.util.spec_from_file_location("app.services.app_services", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules["app.services.app_services"] = module
    spec.loader.exec_module(module)
    return module


class WorkoutServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_log_workout_sends_recommendation_after_commit(self) -> None:
        app_services = _load_app_services()
        events: list[str] = []
        fake_user = SimpleNamespace(id=7, weight_kg=72.0)
        fake_recommendation = SimpleNamespace(
            carbs_min_g=40,
            carbs_max_g=40,
            protein_min_g=20,
            protein_max_g=25,
            fluids_ml_min=700,
            fluids_ml_max=1000,
            sodium_mg_min=300,
            sodium_mg_max=600,
            explanation="test",
        )

        class FakeSession:
            async def commit(self) -> None:
                events.append("commit")

        class FakeSessionContext:
            def __init__(self, session: FakeSession) -> None:
                self._session = session

            async def __aenter__(self) -> FakeSession:
                return self._session

            async def __aexit__(self, exc_type, exc, tb) -> None:
                return None

        class FakeUserRepository:
            def __init__(self, session: object) -> None:
                self.session = session

            async def create_or_update_identity(self, telegram_user_id: int, username: str | None, first_name: str):
                return fake_user

        class FakeWorkoutRepository:
            def __init__(self, session: object) -> None:
                self.session = session

            async def add(self, workout: object):
                events.append("add")
                return workout

        class FakeNotifier:
            async def send_workout_recommendation(self, *, telegram_user_id: int, workout: object, recommendation: object):
                events.append("notify")
                self.telegram_user_id = telegram_user_id
                self.workout = workout
                self.recommendation = recommendation

        notifier = FakeNotifier()
        service = app_services.WorkoutService(
            session_factory=lambda: FakeSessionContext(FakeSession()),
            recommendation_service=SimpleNamespace(recommend=lambda workout, weight_kg: fake_recommendation),
            telegram_notification_service=notifier,
        )

        original_user_repo = app_services.UserRepository
        original_workout_repo = app_services.WorkoutRepository
        try:
            app_services.UserRepository = FakeUserRepository
            app_services.WorkoutRepository = FakeWorkoutRepository
            result = await service.log_workout(
                telegram_user_id=123,
                username="user",
                first_name="Name",
                workout_input=SimpleNamespace(duration_minutes=60, kilojoules=500, intensity="moderate"),
            )
        finally:
            app_services.UserRepository = original_user_repo
            app_services.WorkoutRepository = original_workout_repo

        self.assertEqual(events, ["add", "commit", "notify"])
        self.assertEqual(notifier.telegram_user_id, 123)
        self.assertIs(result.recommendation, fake_recommendation)
