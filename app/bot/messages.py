from decimal import Decimal

from app.db.models import User, Workout
from app.domain.enums import Intensity
from app.dto.recovery import RecoveryRecommendation


def profile_text(user: User) -> str:
    weight = format_weight(user.weight_kg)
    lines = ["Профіль", f"Ім'я: {user.first_name}"]
    if user.username:
        lines.append(f"Користувач: @{user.username}")
    lines.append(f"Вага: {weight}")
    return "\n".join(lines)


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


def intensity_label(intensity: Intensity) -> str:
    mapping = {
        Intensity.EASY: "легка",
        Intensity.MODERATE: "помірна",
        Intensity.HARD: "важка",
    }
    return mapping[intensity]
