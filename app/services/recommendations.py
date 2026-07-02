import random

from app.domain.enums import Intensity
from app.dto.recovery import RecoveryRecommendation
from app.dto.workout import WorkoutInput


class RecoveryRecommendationService:
    def recommend(
        self,
        workout: WorkoutInput,
        weight_kg: float | None,
    ) -> RecoveryRecommendation:
        weight = weight_kg or 70.0

        carbs_target_g = self._carbs_target(workout)

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
            carbs_min_g=carbs_target_g,
            carbs_max_g=carbs_target_g,
            protein_min_g=protein_min_g,
            protein_max_g=protein_max_g,
            fluids_ml_min=self._round_to_50(max(400, fluids_base + fluids_load)),
            fluids_ml_max=self._round_to_50(max(700, fluids_base + fluids_load + 400)),
            sodium_mg_min=self._round_to_50(sodium_min),
            sodium_mg_max=self._round_to_50(sodium_max),
            explanation=self._build_explanation(
                workout=workout,
                carbs_target_g=carbs_target_g,
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
        carbs_target_g: int,
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
        if carbs_target_g == 0:
            return (
                f"{self._intensity_label(workout.intensity)} поїздка: "
                "окремо добирати вуглеводи після неї не обов'язково. "
                f"Зосередься на звичайному прийомі їжі, а {protein_text} протеїну, {fluids_text} рідини і {sodium_text} натрію добери спокійно протягом 2-3 годин. "
                f"Ідея для відновлення: {self._recovery_meal_example(carbs_target_g)}."
            )

        carb_example = self._carb_example(carbs_target_g)
        return (
            f"{self._intensity_label(workout.intensity)} поїздка: "
            f"У перші 10 хв після тренування обов'язково з'їж {carbs_target_g} г вуглеводів. "
            f"{protein_text} протеїну, {fluids_text} рідини і {sodium_text} натрію добери вже без поспіху протягом 2-3 годин. "
            f"Наприклад: {carb_example}."
        )

    def _carbs_target(self, workout: WorkoutInput) -> int:
        if workout.duration_minutes < 30:
            return 0
        if workout.intensity == Intensity.EASY and workout.duration_minutes < 60:
            return 0

        intensity_factor = {
            Intensity.EASY: 0.08,
            Intensity.MODERATE: 0.15,
            Intensity.HARD: 0.18,
        }[workout.intensity]
        carbs_target_g = workout.kilojoules * intensity_factor

        if workout.intensity == Intensity.EASY and workout.duration_minutes < 90:
            carbs_target_g *= 0.5

        carbs_target_rounded = self._round_to_5(carbs_target_g)
        if carbs_target_rounded < 10:
            return 0
        return carbs_target_rounded

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
