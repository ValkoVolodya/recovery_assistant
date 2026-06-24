from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.services.app_services import ProfileService

start_router = Router()


@start_router.message(CommandStart())
async def start_command(message: Message, profile_service: ProfileService) -> None:
    telegram_user = message.from_user
    if telegram_user is None:
        return

    await profile_service.ensure_user(
        telegram_user_id=telegram_user.id,
        username=telegram_user.username,
        first_name=telegram_user.first_name,
    )
    await message.answer(
        "Recovery Assistant готовий.\n"
        "Доступні команди: /profile, /set_weight, /connect_strava, /last_workout.\n"
        "Тренування імпортуються через вебхуки зі Strava."
    )
