import importlib.util
from pathlib import Path
import sys
import types
import unittest
from types import SimpleNamespace


def _load_strava_module():
    sys.modules.pop("app.services.strava", None)
    sys.modules["aiogram"] = types.SimpleNamespace(Bot=object)
    sys.modules["aiogram.client.default"] = types.SimpleNamespace(DefaultBotProperties=object)
    sys.modules["aiogram.enums"] = types.SimpleNamespace(ParseMode=types.SimpleNamespace(HTML="HTML"))
    sys.modules["httpx"] = types.SimpleNamespace(AsyncClient=object, HTTPStatusError=Exception)

    class FakeAsyncSessionMaker:
        def __class_getitem__(cls, item):
            return cls

    sys.modules["sqlalchemy.ext.asyncio"] = types.SimpleNamespace(
        AsyncSession=object,
        async_sessionmaker=FakeAsyncSessionMaker,
    )
    sys.modules["app.config"] = types.SimpleNamespace(Settings=object)
    sys.modules["app.db.models"] = types.SimpleNamespace(StravaConnection=object)
    sys.modules["app.domain.enums"] = types.SimpleNamespace(Intensity=SimpleNamespace(EASY="easy", MODERATE="moderate", HARD="hard"))
    sys.modules["app.dto.workout"] = types.SimpleNamespace(WorkoutInput=object)
    sys.modules["app.repositories.strava_connections"] = types.SimpleNamespace(StravaConnectionRepository=object)
    sys.modules["app.repositories.users"] = types.SimpleNamespace(UserRepository=object)
    sys.modules["app.repositories.workouts"] = types.SimpleNamespace(WorkoutRepository=object)
    sys.modules["app.services.app_services"] = types.SimpleNamespace(WorkoutService=object)
    module_path = Path(__file__).resolve().parents[1] / "app" / "services" / "strava.py"
    spec = importlib.util.spec_from_file_location("app.services.strava", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules["app.services.strava"] = module
    spec.loader.exec_module(module)
    return module


class StravaDisconnectTests(unittest.IsolatedAsyncioTestCase):
    async def test_disconnect_athlete_deletes_existing_connection(self) -> None:
        strava_module = _load_strava_module()
        events: list[str] = []
        fake_user = SimpleNamespace(id=7)
        fake_connection = SimpleNamespace(strava_athlete_id=999, refresh_token="refresh-token")

        class FakeSession:
            async def commit(self) -> None:
                events.append("commit")

        class FakeSessionContext:
            def __init__(self, session: FakeSession) -> None:
                self._session = session

            async def __aenter__(self):
                return self._session

            async def __aexit__(self, exc_type, exc, tb) -> None:
                return None

        class FakeUserRepository:
            def __init__(self, session: object) -> None:
                self.session = session

            async def get_by_telegram_user_id(self, telegram_user_id: int):
                return fake_user

        class FakeConnectionRepository:
            def __init__(self, session: object) -> None:
                self.session = session

            async def get_by_user_id(self, user_id: int):
                return fake_connection

            async def delete(self, connection: object) -> None:
                events.append("delete")

        service = strava_module.StravaService(
            settings=SimpleNamespace(),
            session_factory=lambda: FakeSessionContext(FakeSession()),
            workout_service=SimpleNamespace(),
        )
        service._client = SimpleNamespace(
            revoke_token=self._async_record(events, "revoke"),
        )

        original_user_repo = strava_module.UserRepository
        original_connection_repo = strava_module.StravaConnectionRepository
        try:
            strava_module.UserRepository = FakeUserRepository
            strava_module.StravaConnectionRepository = FakeConnectionRepository
            result = await service.disconnect_athlete(telegram_user_id=123)
        finally:
            strava_module.UserRepository = original_user_repo
            strava_module.StravaConnectionRepository = original_connection_repo

        self.assertTrue(result.disconnected)
        self.assertEqual(events, ["revoke", "delete", "commit"])

    async def test_disconnect_athlete_returns_message_when_not_connected(self) -> None:
        strava_module = _load_strava_module()

        class FakeSession:
            async def commit(self) -> None:
                raise AssertionError("commit should not be called")

        class FakeSessionContext:
            def __init__(self, session: FakeSession) -> None:
                self._session = session

            async def __aenter__(self):
                return self._session

            async def __aexit__(self, exc_type, exc, tb) -> None:
                return None

        class FakeUserRepository:
            def __init__(self, session: object) -> None:
                self.session = session

            async def get_by_telegram_user_id(self, telegram_user_id: int):
                return SimpleNamespace(id=7)

        class FakeConnectionRepository:
            def __init__(self, session: object) -> None:
                self.session = session

            async def get_by_user_id(self, user_id: int):
                return None

        service = strava_module.StravaService(
            settings=SimpleNamespace(),
            session_factory=lambda: FakeSessionContext(FakeSession()),
            workout_service=SimpleNamespace(),
        )

        original_user_repo = strava_module.UserRepository
        original_connection_repo = strava_module.StravaConnectionRepository
        try:
            strava_module.UserRepository = FakeUserRepository
            strava_module.StravaConnectionRepository = FakeConnectionRepository
            result = await service.disconnect_athlete(telegram_user_id=123)
        finally:
            strava_module.UserRepository = original_user_repo
            strava_module.StravaConnectionRepository = original_connection_repo

        self.assertFalse(result.disconnected)
        self.assertEqual(result.message, "Strava і так не підключена.")

    async def test_disconnect_athlete_does_not_delete_when_revoke_fails(self) -> None:
        strava_module = _load_strava_module()
        events: list[str] = []
        fake_user = SimpleNamespace(id=7)
        fake_connection = SimpleNamespace(strava_athlete_id=999, refresh_token="refresh-token")

        class FakeSession:
            async def commit(self) -> None:
                events.append("commit")

        class FakeSessionContext:
            def __init__(self, session: FakeSession) -> None:
                self._session = session

            async def __aenter__(self):
                return self._session

            async def __aexit__(self, exc_type, exc, tb) -> None:
                return None

        class FakeUserRepository:
            def __init__(self, session: object) -> None:
                self.session = session

            async def get_by_telegram_user_id(self, telegram_user_id: int):
                return fake_user

        class FakeConnectionRepository:
            def __init__(self, session: object) -> None:
                self.session = session

            async def get_by_user_id(self, user_id: int):
                return fake_connection

            async def delete(self, connection: object) -> None:
                events.append("delete")

        async def failing_revoke(*args, **kwargs) -> None:
            raise RuntimeError("boom")

        service = strava_module.StravaService(
            settings=SimpleNamespace(),
            session_factory=lambda: FakeSessionContext(FakeSession()),
            workout_service=SimpleNamespace(),
        )
        service._client = SimpleNamespace(revoke_token=failing_revoke)

        original_user_repo = strava_module.UserRepository
        original_connection_repo = strava_module.StravaConnectionRepository
        try:
            strava_module.UserRepository = FakeUserRepository
            strava_module.StravaConnectionRepository = FakeConnectionRepository
            result = await service.disconnect_athlete(telegram_user_id=123)
        finally:
            strava_module.UserRepository = original_user_repo
            strava_module.StravaConnectionRepository = original_connection_repo

        self.assertFalse(result.disconnected)
        self.assertEqual(events, [])
        self.assertIn("Не вдалося коректно відкликати доступ Strava", result.message)

    def _async_record(self, events: list[str], name: str):
        async def _inner(*args, **kwargs) -> None:
            events.append(name)

        return _inner
