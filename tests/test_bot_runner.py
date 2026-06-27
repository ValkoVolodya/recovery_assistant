import importlib
import sys
import types
import unittest
from types import SimpleNamespace


def _load_bot_runner():
    sys.modules.pop("app.bot.runner", None)
    sys.modules["aiogram"] = types.SimpleNamespace(Bot=object, Dispatcher=object)
    sys.modules["aiogram.client.default"] = types.SimpleNamespace(DefaultBotProperties=object)
    sys.modules["aiogram.enums"] = types.SimpleNamespace(ParseMode=types.SimpleNamespace(HTML="HTML"))
    sys.modules["aiogram.fsm.storage.memory"] = types.SimpleNamespace(MemoryStorage=object)
    sys.modules["app.bot.router"] = types.SimpleNamespace(build_router=lambda: object())
    return importlib.import_module("app.bot.runner")


class TelegramWebhookTests(unittest.IsolatedAsyncioTestCase):
    async def test_ensure_telegram_webhook_sets_expected_url(self) -> None:
        runner = _load_bot_runner()
        calls: list[tuple[str, object]] = []

        class FakeBot:
            async def set_webhook(self, *, url: str, allowed_updates: list[str]) -> None:
                calls.append((url, allowed_updates))

        runtime = SimpleNamespace(settings=SimpleNamespace(app_base_url="https://example.com"))
        bot_runtime = SimpleNamespace(
            bot=FakeBot(),
            dispatcher=SimpleNamespace(resolve_used_update_types=lambda: ["message", "callback_query"]),
        )

        await runner.ensure_telegram_webhook(bot_runtime, runtime)

        self.assertEqual(
            calls,
            [("https://example.com/telegram/webhook", ["message", "callback_query"])],
        )

    def test_get_telegram_webhook_url_rejects_missing_base_url(self) -> None:
        runner = _load_bot_runner()

        with self.assertRaisesRegex(RuntimeError, "APP_BASE_URL is required"):
            runner.get_telegram_webhook_url(None)
