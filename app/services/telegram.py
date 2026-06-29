import logging

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.bot.messages import workout_summary_text
from app.config import Settings
from app.db.models import Workout
from app.dto.recovery import RecoveryRecommendation

logger = logging.getLogger(__name__)


class TelegramNotificationService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def send_workout_recommendation(
        self,
        telegram_user_id: int,
        workout: Workout,
        recommendation: RecoveryRecommendation,
    ) -> None:
        bot = Bot(
            token=self._settings.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        try:
            await bot.send_message(
                chat_id=telegram_user_id,
                text=workout_summary_text(workout, recommendation),
            )
        except Exception:
            logger.exception("Failed to send workout recommendation to telegram_user_id=%s", telegram_user_id)
        finally:
            await bot.session.close()
