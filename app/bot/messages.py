from decimal import Decimal

from app.db.models import User, Workout
from app.domain.enums import Intensity
from app.dto.recovery import RecoveryRecommendation


def profile_text(user: User) -> str:
    weight = format_weight(user.weight_kg)
    ftp = format_ftp(user.ftp_watts)
    lines = ["Профіль", f"Ім'я: {user.first_name}"]
    if user.username:
        lines.append(f"Користувач: @{user.username}")
    lines.append(f"Вага: {weight}")
    lines.append(f"FTP: {ftp}")
    return "\n".join(lines)


def onboarding_welcome_text(*, has_weight: bool) -> str:
    if has_weight:
        return (
            "👋 Вітаю в Recovery Assistant.\n\n"
            "Я допомагаю після тренувань: підтягую поїздки зі Strava і одразу надсилаю план відновлення.\n\n"
            "Що далі:\n"
            "1. Підключи Strava\n"
            "2. Після наступної поїздки я сам надішлю рекомендацію\n\n"
            "Команди: /profile, /set_weight, /set_ftp, /connect_strava, /disconnect_strava, /last_workout."
        )
    return (
        "👋 Вітаю в Recovery Assistant.\n\n"
        "Я допомагаю після тренувань: підтягую поїздки зі Strava і одразу надсилаю план відновлення.\n\n"
        "Налаштуємо все за хвилину.\n"
        "Крок 1 з 2: надішли свою вагу в кг, наприклад `72.5`."
    )


def post_weight_next_step_text(*, weight_text: str, strava_connect_url: str | None) -> str:
    if strava_connect_url is None:
        return (
            f"✅ Вагу збережено: {weight_text}.\n\n"
            "Крок 2 з 2: підключи Strava командою /connect_strava, коли вона буде налаштована."
        )
    return (
        f"✅ Вагу збережено: {weight_text}.\n\n"
        "Крок 2 з 2: підключи Strava за цим посиланням:\n"
        f"{strava_connect_url}\n\n"
        "Після наступної поїздки я сам надішлю рекомендацію в чат."
    )


def workout_summary_text(workout: Workout, recommendation: RecoveryRecommendation) -> str:
    return (
        "✅ План відновлення\n\n"
        "📝 Що робити\n"
        f"{recommendation.explanation}\n\n"
        "📌 Деталі тренування\n"
        f"• Інтенсивність: {intensity_label(workout.intensity)}\n"
        f"• Тривалість: {workout.duration_minutes} хв\n"
        f"• Робота: {workout.kilojoules} кДж"
    )


def format_weight(weight: Decimal | float | None) -> str:
    if weight is None:
        return "не вказано"
    return f"{float(weight):.1f} кг"


def format_ftp(ftp_watts: int | None) -> str:
    if ftp_watts is None:
        return "не вказано"
    return f"{ftp_watts} Вт"


def intensity_label(intensity: Intensity) -> str:
    mapping = {
        Intensity.EASY: "легка",
        Intensity.MODERATE: "помірна",
        Intensity.HARD: "важка",
    }
    return mapping[intensity]
