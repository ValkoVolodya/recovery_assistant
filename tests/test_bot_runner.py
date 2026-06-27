import importlib
import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import patch


def _load_bot_runner():
    sys.modules.pop("app.bot.runner", None)
    sys.modules["aiogram"] = types.SimpleNamespace(Bot=object, Dispatcher=object)
    sys.modules["aiogram.client.default"] = types.SimpleNamespace(DefaultBotProperties=object)
    sys.modules["aiogram.enums"] = types.SimpleNamespace(ParseMode=types.SimpleNamespace(HTML="HTML"))
    sys.modules["aiogram.fsm.storage.memory"] = types.SimpleNamespace(MemoryStorage=object)
    sys.modules["app.bot.router"] = types.SimpleNamespace(build_router=lambda: object())
    sys.modules["app.runtime"] = types.SimpleNamespace(AppRuntime=object)
    return importlib.import_module("app.bot.runner")


class RunBotTests(unittest.IsolatedAsyncioTestCase):
    async def test_run_bot_deletes_webhook_before_polling(self) -> None:
        runner = _load_bot_runner()
        calls: list[str] = []

        class FakeBot:
            def __init__(self, token: str, default: object) -> None:
                self.token = token
                self.default = default
                self.session = SimpleNamespace(close=self._close)

            async def delete_webhook(self, drop_pending_updates: bool) -> None:
                calls.append(f"delete:{drop_pending_updates}")

            async def _close(self) -> None:
                calls.append("close")

        class FakeDispatcher:
            async def start_polling(self, bot: object) -> None:
                calls.append("poll")

        runtime = SimpleNamespace(settings=SimpleNamespace(bot_token="token"))

        with (
            patch.object(runner, "Bot", FakeBot),
            patch.object(runner, "DefaultBotProperties", side_effect=lambda **kwargs: kwargs),
            patch.object(runner, "build_dispatcher", return_value=FakeDispatcher()),
        ):
            await runner.run_bot(runtime)

        self.assertEqual(calls, ["delete:False", "poll", "close"])
