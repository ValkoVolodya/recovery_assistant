from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.messages import workout_summary_text
from app.services.app_services import WorkoutService

workout_router = Router()


@workout_router.message(Command("last_workout"))
async def last_workout_command(message: Message, workout_service: WorkoutService) -> None:
    telegram_user = message.from_user
    if telegram_user is None:
        return

    result = await workout_service.get_last_workout(telegram_user.id)
    if result is None:
        await message.answer("Профіль ще не створено. Спочатку виконайте /start.")
        return
    if result.workout is None or result.recommendation is None:
        await message.answer(
            "Тренування ще не імпортовано. Підключіть Strava та дочекайтеся наступного вебхука про активність."
        )
        return
    await message.answer(workout_summary_text(result.workout, result.recommendation))
