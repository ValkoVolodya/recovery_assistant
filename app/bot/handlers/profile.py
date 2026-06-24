from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.fsm import SetWeightStates
from app.bot.messages import format_weight, profile_text
from app.services.app_services import ProfileService

profile_router = Router()


@profile_router.message(Command("profile"))
async def profile_command(message: Message, profile_service: ProfileService) -> None:
    telegram_user = message.from_user
    if telegram_user is None:
        return

    user = await profile_service.get_profile(telegram_user.id)
    if user is None:
        await message.answer("Профіль ще не створено. Спочатку виконайте /start.")
        return
    await message.answer(profile_text(user))


@profile_router.message(Command("set_weight"))
async def set_weight_command(message: Message, state: FSMContext) -> None:
    await state.set_state(SetWeightStates.waiting_for_weight)
    await message.answer("Надішліть вагу в кг, наприклад: 72.5")


@profile_router.message(SetWeightStates.waiting_for_weight)
async def set_weight_value(
    message: Message,
    state: FSMContext,
    profile_service: ProfileService,
) -> None:
    telegram_user = message.from_user
    if telegram_user is None or message.text is None:
        return

    try:
        weight = float(message.text.strip().replace(",", "."))
    except ValueError:
        await message.answer("Вага має бути числом у кілограмах.")
        return

    if not 30 <= weight <= 250:
        await message.answer("Вага має бути в межах від 30 до 250 кг.")
        return

    user = await profile_service.set_weight(
        telegram_user_id=telegram_user.id,
        username=telegram_user.username,
        first_name=telegram_user.first_name,
        weight_kg=weight,
    )
    await state.clear()
    await message.answer(f"Вагу оновлено: {format_weight(user.weight_kg)}.")
