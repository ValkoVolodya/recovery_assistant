from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.fsm import SetWeightStates
from app.bot.messages import onboarding_welcome_text
from app.services.app_services import ProfileService
from app.services.strava import StravaService

start_router = Router()


@start_router.message(CommandStart())
async def start_command(
    message: Message,
    state: FSMContext,
    profile_service: ProfileService,
    strava_service: StravaService,
) -> None:
    telegram_user = message.from_user
    if telegram_user is None:
        return

    user = await profile_service.ensure_user(
        telegram_user_id=telegram_user.id,
        username=telegram_user.username,
        first_name=telegram_user.first_name,
    )
    has_weight = user.weight_kg is not None
    await message.answer(onboarding_welcome_text(has_weight=has_weight))
    if not has_weight:
        await state.set_state(SetWeightStates.waiting_for_weight)
        return

    if not strava_service.is_configured():
        await message.answer("Strava ще не налаштована на сервері. Коли буде готово, використай /connect_strava.")
        return

    status = await strava_service.get_connection_status(telegram_user.id)
    await message.answer(status.message)
