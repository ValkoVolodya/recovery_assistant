from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.fsm import SetFtpStates, SetWeightStates
from app.bot.messages import format_ftp, format_weight, post_weight_next_step_text, profile_text
from app.services.app_services import ProfileService
from app.services.strava import StravaService

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


@profile_router.message(Command("set_ftp"))
async def set_ftp_command(message: Message, state: FSMContext) -> None:
    await state.set_state(SetFtpStates.waiting_for_ftp)
    await message.answer("Надішліть FTP у ватах, наприклад: 265")


@profile_router.message(SetWeightStates.waiting_for_weight)
async def set_weight_value(
    message: Message,
    state: FSMContext,
    profile_service: ProfileService,
    strava_service: StravaService,
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
    connect_url = None
    if strava_service.is_configured():
        connect_url = strava_service.build_connect_url(telegram_user.id)
    await message.answer(
        post_weight_next_step_text(
            weight_text=format_weight(user.weight_kg),
            strava_connect_url=connect_url,
        )
    )


@profile_router.message(SetFtpStates.waiting_for_ftp)
async def set_ftp_value(
    message: Message,
    state: FSMContext,
    profile_service: ProfileService,
) -> None:
    telegram_user = message.from_user
    if telegram_user is None or message.text is None:
        return

    try:
        ftp_watts = int(message.text.strip())
    except ValueError:
        await message.answer("FTP має бути цілим числом у ватах.")
        return

    if not 100 <= ftp_watts <= 600:
        await message.answer("FTP має бути в межах від 100 до 600 Вт.")
        return

    user = await profile_service.set_ftp(
        telegram_user_id=telegram_user.id,
        username=telegram_user.username,
        first_name=telegram_user.first_name,
        ftp_watts=ftp_watts,
    )
    await state.clear()
    await message.answer(f"✅ FTP збережено: {format_ftp(user.ftp_watts)}.")
