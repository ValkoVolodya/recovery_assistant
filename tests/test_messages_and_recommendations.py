import importlib.util
from pathlib import Path
import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.domain.enums import Intensity


def _load_messages_module():
    sys.modules["app.db.models"] = types.SimpleNamespace(User=object, Workout=object)
    sys.modules["app.dto.recovery"] = types.SimpleNamespace(RecoveryRecommendation=object)
    module_path = Path(__file__).resolve().parents[1] / "app" / "bot" / "messages.py"
    spec = importlib.util.spec_from_file_location("app.bot.messages", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_recommendations_module():
    sys.modules["app.dto.recovery"] = types.SimpleNamespace(RecoveryRecommendation=object)
    sys.modules["app.dto.workout"] = types.SimpleNamespace(WorkoutInput=object)
    module_path = Path(__file__).resolve().parents[1] / "app" / "services" / "recommendations.py"
    spec = importlib.util.spec_from_file_location("app.services.recommendations", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


class RecommendationPresentationTests(unittest.TestCase):
    def test_workout_summary_text_is_structured(self) -> None:
        messages = _load_messages_module()
        workout = SimpleNamespace(duration_minutes=95, kilojoules=1100, intensity=Intensity.MODERATE)
        recommendation = SimpleNamespace(
            carbs_min_g=60,
            carbs_max_g=60,
            protein_min_g=20,
            protein_max_g=25,
            fluids_ml_min=900,
            fluids_ml_max=1300,
            sodium_mg_min=500,
            sodium_mg_max=900,
            explanation="Помірна поїздка: у перші 10 хв після тренування треба з'їсти 60 г вуглеводів.",
        )

        text = messages.workout_summary_text(workout, recommendation)

        self.assertIn("✅ План відновлення", text)
        self.assertIn("📝 Що робити", text)
        self.assertIn("📌 Деталі тренування", text)

    def test_carb_example_uses_variant_pool(self) -> None:
        recommendations = _load_recommendations_module()
        service = recommendations.RecoveryRecommendationService()

        with patch.object(recommendations.random, "choice", side_effect=lambda options: options[-1]):
            example = service._carb_example(35)

        self.assertEqual(example, "вівсянка швидкого приготування з бананом")

    def test_explanation_highlights_carb_timing_only(self) -> None:
        recommendations = _load_recommendations_module()
        service = recommendations.RecoveryRecommendationService()

        with patch.object(recommendations.random, "choice", side_effect=lambda options: options[0]):
            explanation = service._build_explanation(
                workout=SimpleNamespace(intensity=Intensity.MODERATE),
                carbs_target_g=60,
                protein_min_g=20,
                protein_max_g=25,
                fluids_ml_min=900,
                fluids_ml_max=1300,
                sodium_mg_min=500,
                sodium_mg_max=900,
            )

        self.assertIn("У перші 10 хв після тренування обов'язково з'їж 60 г вуглеводів.", explanation)
        self.assertIn("протягом 2-3 годин", explanation)
        self.assertIn("20-25 г протеїну", explanation)
        self.assertIn("900-1300 мл рідини", explanation)
        self.assertIn("500-900 мг натрію", explanation)
