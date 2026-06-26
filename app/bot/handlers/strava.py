from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services.strava import StravaService

strava_router = Router()


@strava_router.message(Command("connect_strava"))
async def connect_strava_command(message: Message, strava_service: StravaService) -> None:
    telegram_user = message.from_user
    if telegram_user is None:
        return

    if not strava_service.is_configured():
        await message.answer("Strava ще не налаштована. Спочатку заповніть Strava змінні в .env.")
        return

    status = await strava_service.get_connection_status(telegram_user.id)
    if status.connected:
        await message.answer(status.message)
        return

    connect_url = strava_service.build_connect_url(telegram_user.id)
    await message.answer(
        f"{status.message}\n\n"
        "Відкрий це посилання, авторизуй Strava і повернись у бот:\n"
        f"{connect_url}"
    )
