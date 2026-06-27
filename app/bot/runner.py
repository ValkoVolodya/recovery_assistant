from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
from typing import Any

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.bot.router import build_router

logger = logging.getLogger(__name__)


@dataclass
class TelegramBotRuntime:
    bot: Bot
    dispatcher: Dispatcher


def build_dispatcher(runtime: Any) -> Dispatcher:
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(build_router())
    dispatcher["profile_service"] = runtime.profile_service
    dispatcher["workout_service"] = runtime.workout_service
    dispatcher["strava_service"] = runtime.strava_service
    return dispatcher


def build_bot_runtime(runtime: Any) -> TelegramBotRuntime:
    bot = Bot(
        token=runtime.settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = build_dispatcher(runtime)
    return TelegramBotRuntime(bot=bot, dispatcher=dispatcher)


def get_telegram_webhook_url(app_base_url: str | None) -> str:
    if not app_base_url:
        raise RuntimeError("APP_BASE_URL is required for Telegram webhook mode")
    return f"{app_base_url.rstrip('/')}/telegram/webhook"


async def ensure_telegram_webhook(bot_runtime: TelegramBotRuntime, runtime: Any) -> None:
    webhook_url = get_telegram_webhook_url(runtime.settings.app_base_url)
    logger.info("Configuring Telegram webhook url=%s", webhook_url)
    await bot_runtime.bot.set_webhook(
        url=webhook_url,
        allowed_updates=bot_runtime.dispatcher.resolve_used_update_types(),
    )
    logger.info("Telegram webhook configured url=%s", webhook_url)


async def ensure_telegram_webhook_with_retry(
    bot_runtime: TelegramBotRuntime,
    runtime: Any,
    *,
    initial_delay_seconds: float = 5.0,
    max_attempts: int = 5,
    retry_delay_seconds: float = 15.0,
) -> None:
    if initial_delay_seconds > 0:
        await asyncio.sleep(initial_delay_seconds)

    for attempt in range(1, max_attempts + 1):
        try:
            await ensure_telegram_webhook(bot_runtime, runtime)
            return
        except Exception:
            logger.exception(
                "Failed to configure Telegram webhook on attempt %s/%s",
                attempt,
                max_attempts,
            )
            if attempt == max_attempts:
                return
            await asyncio.sleep(retry_delay_seconds)


async def close_bot(bot_runtime: TelegramBotRuntime) -> None:
    await bot_runtime.bot.session.close()
