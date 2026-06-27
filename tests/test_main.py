import asyncio
import importlib
import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import patch


def _load_app_main():
    sys.modules.pop("app.main", None)
    sys.modules["uvicorn"] = types.SimpleNamespace(Config=object, Server=object)
    sys.modules["app.bot.runner"] = types.SimpleNamespace(run_bot=lambda runtime: None)
    sys.modules["app.runtime"] = types.SimpleNamespace(build_runtime=lambda: None)
    sys.modules["app.web"] = types.SimpleNamespace(create_app=lambda runtime: None)
    return importlib.import_module("app.main")


class RunLifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def test_run_fails_when_bot_stops_cleanly(self) -> None:
        app_main = _load_app_main()
        runtime = SimpleNamespace(
            settings=SimpleNamespace(app_host="127.0.0.1", app_port=8000),
            engine=SimpleNamespace(dispose=self._async_noop),
            strava_service=SimpleNamespace(ensure_webhook_subscription_with_retry=self._neverending_task),
        )
        serve_started = asyncio.Event()
        serve_cancelled = asyncio.Event()

        async def fake_run_bot(_: object) -> None:
            return None

        async def fake_serve(self) -> None:
            serve_started.set()
            try:
                await asyncio.Future()
            except asyncio.CancelledError:
                serve_cancelled.set()
                raise

        class FakeServer:
            def __init__(self, config: object) -> None:
                self.config = config
                self.should_exit = False

            serve = fake_serve

        with (
            patch.object(app_main, "build_runtime", return_value=runtime),
            patch.object(app_main, "create_app", return_value=object()),
            patch.object(app_main, "run_bot", side_effect=fake_run_bot),
            patch.object(app_main.uvicorn, "Config", side_effect=lambda *args, **kwargs: object()),
            patch.object(app_main.uvicorn, "Server", side_effect=FakeServer),
        ):
            with self.assertRaisesRegex(RuntimeError, "Telegram polling stopped unexpectedly"):
                await app_main.run()

        self.assertTrue(serve_started.is_set())
        self.assertTrue(serve_cancelled.is_set())

    async def _async_noop(self) -> None:
        return None

    async def _neverending_task(self) -> None:
        await asyncio.Future()
