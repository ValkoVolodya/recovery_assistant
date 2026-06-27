import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.bot.router import build_router
from app.runtime import AppRuntime

logger = logging.getLogger(__name__)


def build_dispatcher(runtime: AppRuntime) -> Dispatcher:
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(build_router())
    dispatcher["profile_service"] = runtime.profile_service
    dispatcher["workout_service"] = runtime.workout_service
    dispatcher["strava_service"] = runtime.strava_service
    return dispatcher


async def run_bot(runtime: AppRuntime) -> None:
    bot = Bot(
        token=runtime.settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = build_dispatcher(runtime)

    try:
        logger.info("Deleting Telegram webhook before polling startup")
        await bot.delete_webhook(drop_pending_updates=False)
        logger.info("Starting Telegram polling")
        await dispatcher.start_polling(bot)
        logger.warning("Telegram polling stopped without raising an exception")
    finally:
        await bot.session.close()
