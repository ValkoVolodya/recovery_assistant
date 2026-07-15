from dataclasses import dataclass
import random

from app.domain.enums import Intensity
from app.dto.recovery import RecoveryRecommendation
from app.dto.workout import WorkoutInput


@dataclass(frozen=True)
class CarbRule:
    ride_min: int
    ride_max: int
    tss_per_hour_min: int
    tss_per_hour_max: int
    carbs_min_per_kg: float
    carbs_max_per_kg: float

CARB_RULES = (
    CarbRule(ride_min=0, ride_max=45, tss_per_hour_min=0, tss_per_hour_max=50, carbs_min_per_kg=0.3, carbs_max_per_kg=0.4),
    CarbRule(ride_min=0, ride_max=45, tss_per_hour_min=50, tss_per_hour_max=60, carbs_min_per_kg=0.4, carbs_max_per_kg=0.5),
    CarbRule(ride_min=0, ride_max=45, tss_per_hour_min=61, tss_per_hour_max=72, carbs_min_per_kg=0.5, carbs_max_per_kg=0.6),
    CarbRule(ride_min=0, ride_max=45, tss_per_hour_min=73, tss_per_hour_max=999, carbs_min_per_kg=0.5, carbs_max_per_kg=0.7),
    CarbRule(ride_min=46, ride_max=75, tss_per_hour_min=0, tss_per_hour_max=50, carbs_min_per_kg=0.3, carbs_max_per_kg=0.4),
    CarbRule(ride_min=46, ride_max=75, tss_per_hour_min=50, tss_per_hour_max=60, carbs_min_per_kg=0.4, carbs_max_per_kg=0.5),
    CarbRule(ride_min=46, ride_max=75, tss_per_hour_min=61, tss_per_hour_max=72, carbs_min_per_kg=0.5, carbs_max_per_kg=0.6),
    CarbRule(ride_min=46, ride_max=75, tss_per_hour_min=73, tss_per_hour_max=999, carbs_min_per_kg=0.6, carbs_max_per_kg=0.7),
    CarbRule(ride_min=76, ride_max=120, tss_per_hour_min=0, tss_per_hour_max=50, carbs_min_per_kg=0.4, carbs_max_per_kg=0.5),
    CarbRule(ride_min=76, ride_max=120, tss_per_hour_min=50, tss_per_hour_max=60, carbs_min_per_kg=0.5, carbs_max_per_kg=0.6),
    CarbRule(ride_min=76, ride_max=120, tss_per_hour_min=61, tss_per_hour_max=72, carbs_min_per_kg=0.6, carbs_max_per_kg=0.7),
    CarbRule(ride_min=76, ride_max=120, tss_per_hour_min=73, tss_per_hour_max=999, carbs_min_per_kg=0.7, carbs_max_per_kg=0.8),
    CarbRule(ride_min=121, ride_max=180, tss_per_hour_min=0, tss_per_hour_max=50, carbs_min_per_kg=0.8, carbs_max_per_kg=0.9),
    CarbRule(ride_min=121, ride_max=180, tss_per_hour_min=50, tss_per_hour_max=60, carbs_min_per_kg=0.9, carbs_max_per_kg=1.0),
    CarbRule(ride_min=121, ride_max=180, tss_per_hour_min=61, tss_per_hour_max=72, carbs_min_per_kg=1.0, carbs_max_per_kg=1.1),
    CarbRule(ride_min=121, ride_max=180, tss_per_hour_min=73, tss_per_hour_max=999, carbs_min_per_kg=1.1, carbs_max_per_kg=1.2),
    CarbRule(ride_min=181, ride_max=240, tss_per_hour_min=0, tss_per_hour_max=50, carbs_min_per_kg=0.8, carbs_max_per_kg=0.9),
    CarbRule(ride_min=181, ride_max=240, tss_per_hour_min=50, tss_per_hour_max=60, carbs_min_per_kg=1.0, carbs_max_per_kg=1.1),
    CarbRule(ride_min=181, ride_max=240, tss_per_hour_min=61, tss_per_hour_max=72, carbs_min_per_kg=1.1, carbs_max_per_kg=1.2),
    CarbRule(ride_min=181, ride_max=240, tss_per_hour_min=73, tss_per_hour_max=999, carbs_min_per_kg=1.2, carbs_max_per_kg=1.2),
    CarbRule(ride_min=241, ride_max=999, tss_per_hour_min=0, tss_per_hour_max=50, carbs_min_per_kg=0.8, carbs_max_per_kg=0.9),
    CarbRule(ride_min=241, ride_max=999, tss_per_hour_min=50, tss_per_hour_max=60, carbs_min_per_kg=1.0, carbs_max_per_kg=1.1),
    CarbRule(ride_min=241, ride_max=999, tss_per_hour_min=61, tss_per_hour_max=72, carbs_min_per_kg=1.1, carbs_max_per_kg=1.2),
    CarbRule(ride_min=241, ride_max=999, tss_per_hour_min=73, tss_per_hour_max=999, carbs_min_per_kg=1.2, carbs_max_per_kg=1.2),
)


class RecoveryRecommendationService:
    def recommend(
        self,
        workout: WorkoutInput,
        weight_kg: float | None,
        ftp_watts: int | None = None,
    ) -> RecoveryRecommendation:
        weight = weight_kg or 70.0

        carbs_min_g, carbs_max_g = self._carbs_range(workout, weight, ftp_watts)

        protein_factor_min = 0.25
        protein_factor_max = 0.35
        if workout.intensity == Intensity.HARD:
            protein_factor_max = 0.4

        fluids_base = 500
        fluids_load = workout.duration_minutes * 7
        if workout.intensity == Intensity.EASY:
            fluids_load -= 100
        elif workout.intensity == Intensity.HARD:
            fluids_load += 250

        sodium_min = 300
        sodium_max = 600
        if workout.duration_minutes >= 90:
            sodium_min += 200
            sodium_max += 300
        if workout.intensity == Intensity.HARD:
            sodium_min += 200
            sodium_max += 300

        protein_min_g = self._round_to_5(weight * protein_factor_min)
        protein_max_g = self._round_to_5(weight * protein_factor_max)

        recommendation = RecoveryRecommendation(
            carbs_min_g=carbs_min_g,
            carbs_max_g=carbs_max_g,
            protein_min_g=protein_min_g,
            protein_max_g=protein_max_g,
            fluids_ml_min=self._round_to_50(max(400, fluids_base + fluids_load)),
            fluids_ml_max=self._round_to_50(max(700, fluids_base + fluids_load + 400)),
            sodium_mg_min=self._round_to_50(sodium_min),
            sodium_mg_max=self._round_to_50(sodium_max),
            explanation=self._build_explanation(
                workout=workout,
                carbs_min_g=carbs_min_g,
                carbs_max_g=carbs_max_g,
                protein_min_g=protein_min_g,
                protein_max_g=protein_max_g,
                fluids_ml_min=self._round_to_50(max(400, fluids_base + fluids_load)),
                fluids_ml_max=self._round_to_50(max(700, fluids_base + fluids_load + 400)),
                sodium_mg_min=self._round_to_50(sodium_min),
                sodium_mg_max=self._round_to_50(sodium_max),
            ),
        )
        return recommendation

    def _build_explanation(
        self,
        workout: WorkoutInput,
        carbs_min_g: int,
        carbs_max_g: int,
        protein_min_g: int,
        protein_max_g: int,
        fluids_ml_min: int,
        fluids_ml_max: int,
        sodium_mg_min: int,
        sodium_mg_max: int,
    ) -> str:
        protein_text = (
            f"{protein_min_g} г"
            if protein_min_g == protein_max_g
            else f"{protein_min_g}-{protein_max_g} г"
        )
        fluids_text = f"{fluids_ml_min}-{fluids_ml_max} мл"
        sodium_text = f"{sodium_mg_min}-{sodium_mg_max} мг"
        carbs_text = (
            f"{carbs_min_g} г"
            if carbs_min_g == carbs_max_g
            else f"{carbs_min_g}-{carbs_max_g} г"
        )
        if carbs_max_g == 0:
            return (
                f"{self._intensity_label(workout.intensity)} поїздка: "
                "окремо добирати вуглеводи після неї не обов'язково. "
                f"Зосередься на звичайному прийомі їжі, а {protein_text} протеїну, {fluids_text} рідини і {sodium_text} натрію добери спокійно протягом 2-3 годин. \n"
                f"Ідея для відновлення: {self._recovery_meal_example(carbs_max_g)}."
            )

        carb_example = self._carb_example(carbs_max_g)
        return (
            f"{self._intensity_label(workout.intensity)} поїздка: "
            f"У перші 10 хв після тренування обов'язково з'їж {carbs_text} вуглеводів. \n"
            f"{protein_text} протеїну, {fluids_text} рідини і {sodium_text} натрію добери вже без поспіху протягом 2-3 годин. \n"
            f"Наприклад: {carb_example}."
        )

    def _carbs_range(
        self,
        workout: WorkoutInput,
        weight_kg: float,
        ftp_watts: int | None,
    ) -> tuple[int, int]:
        estimated_tss_per_hour = self._estimate_tss_per_hour(workout, ftp_watts)
        rule = self._carb_rule(workout.duration_minutes, estimated_tss_per_hour)
        carbs_min_g = self._round_to_5(weight_kg * rule.carbs_min_per_kg)
        carbs_max_g = self._round_to_5(weight_kg * rule.carbs_max_per_kg)
        return carbs_min_g, max(carbs_min_g, carbs_max_g)

    def _estimate_tss_per_hour(self, workout: WorkoutInput, ftp_watts: int | None) -> int:
        if workout.weighted_average_watts is not None and ftp_watts:
            intensity_factor = workout.weighted_average_watts / ftp_watts
            return max(0, round(100 * intensity_factor * intensity_factor))

        fallback_tss_per_hour = {
            Intensity.EASY: 45,
            Intensity.MODERATE: 60,
            Intensity.HARD: 75,
        }
        return fallback_tss_per_hour[workout.intensity]

    def _carb_rule(self, duration_minutes: int, tss_per_hour: int) -> CarbRule:
        for rule in CARB_RULES:
            if (
                rule.ride_min <= duration_minutes <= rule.ride_max
                and rule.tss_per_hour_min <= tss_per_hour <= rule.tss_per_hour_max
            ):
                return rule
        return CARB_RULES[-1]

    def _carb_example(self, carbs_target_g: int) -> str:
        return random.choice(self._carb_examples(carbs_target_g))

    def _recovery_meal_example(self, carbs_target_g: int) -> str:
        return random.choice(self._recovery_meal_examples(carbs_target_g))

    def _carb_examples(self, carbs_target_g: int) -> list[str]:
        if carbs_target_g <= 40:
            return [
                "банан і питний йогурт",
                "йогурт з ягодами і гранолою",
                "рисові хлібці з медом і кефір",
                "вівсянка швидкого приготування з бананом",
            ]
        if carbs_target_g <= 60:
            return [
                "банан, солодкий батончик або 2 тости з джемом",
                "сендвіч із джемом і склянка соку",
                "вівсянка з медом і бананом",
                "рисовий пудинг і фрукт",
            ]
        if carbs_target_g <= 90:
            return [
                "булка з медом, рисовий пудинг або велика порція пластівців із молоком",
                "велика миска пластівців із молоком і бананом",
                "два тости з джемом, йогурт і сік",
                "рис, фруктовий йогурт і банан",
            ]
        return [
            "велика порція рису, пасти або 2 тости з джемом",
            "паста з томатним соусом і солодкий напій",
            "велика порція рису з фруктом і йогуртом",
            "солодка булка з медом, банан і шоколадне молоко",
        ]

    def _recovery_meal_examples(self, carbs_target_g: int) -> list[str]:
        if carbs_target_g == 0:
            return [
                "омлет і тост, плюс вода",
                "грецький йогурт з ягодами",
                "сир кисломолочний і фрукт",
                "сендвіч з яйцем і чай",
            ]
        if carbs_target_g <= 40:
            return [
                "банан, йогурт і вода",
                "вівсянка з ягодами",
                "рисові хлібці з медом і питний йогурт",
                "кефір і булочка з джемом",
            ]
        if carbs_target_g <= 60:
            return [
                "вівсянка з бананом і медом",
                "сендвіч з джемом і йогурт",
                "рисовий пудинг і фрукт",
                "тости з медом і шоколадне молоко",
            ]
        if carbs_target_g <= 90:
            return [
                "булка з медом, банан і йогурт",
                "велика миска пластівців із молоком",
                "рис з фруктами і питний йогурт",
                "два тости з джемом і рисовий пудинг",
            ]
        return [
            "велика тарілка рису і солодкий йогурт",
            "паста, банан і напій з вуглеводами",
            "два тости з джемом і шоколадне молоко",
            "велика порція пластівців, тости з медом і фрукт",
        ]

    def _round_to_5(self, value: float) -> int:
        return int(round(value / 5) * 5)

    def _round_to_50(self, value: float) -> int:
        return int(round(value / 50) * 50)

    def _intensity_label(self, intensity: Intensity) -> str:
        mapping = {
            Intensity.EASY: "Легка",
            Intensity.MODERATE: "Помірна",
            Intensity.HARD: "Важка",
        }
        return mapping[intensity]
