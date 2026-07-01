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
    carbs_text = (
        "не обов'язково окремо добирати"
        if recommendation.carbs_min_g == 0 and recommendation.carbs_max_g == 0
        else
        f"{recommendation.carbs_min_g} г"
        if recommendation.carbs_min_g == recommendation.carbs_max_g
        else f"{recommendation.carbs_min_g}-{recommendation.carbs_max_g} г"
    )
    return (
        "🚴 Тренування збережено\n\n"
        "📊 Навантаження\n"
        f"• Тривалість: {workout.duration_minutes} хв\n"
        f"• Робота: {workout.kilojoules} кДж\n"
        f"• Інтенсивність: {intensity_label(workout.intensity)}\n\n"
        "🥤 Відновлення\n"
        f"• Вуглеводи: {carbs_text}\n"
        f"• Білок: {recommendation.protein_min_g}-{recommendation.protein_max_g} г\n"
        f"• Рідина: {recommendation.fluids_ml_min}-{recommendation.fluids_ml_max} мл\n"
        f"• Натрій: {recommendation.sodium_mg_min}-{recommendation.sodium_mg_max} мг\n\n"
        "📝 Порада\n"
        f"{recommendation.explanation}"
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
