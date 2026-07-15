import importlib.util
from pathlib import Path
import sys
import types
import unittest


def _load_messages_module():
    sys.modules["app.db.models"] = types.SimpleNamespace(User=object, Workout=object)
    sys.modules["app.dto.recovery"] = types.SimpleNamespace(RecoveryRecommendation=object)
    module_path = Path(__file__).resolve().parents[1] / "app" / "bot" / "messages.py"
    spec = importlib.util.spec_from_file_location("app.bot.messages", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


class OnboardingMessageTests(unittest.TestCase):
    def test_welcome_text_without_weight_prompts_for_next_step(self) -> None:
        messages = _load_messages_module()

        text = messages.onboarding_welcome_text(has_weight=False)

        self.assertIn("Крок 1 з 2", text)
        self.assertIn("надішли свою вагу", text)

    def test_post_weight_text_can_include_strava_url(self) -> None:
        messages = _load_messages_module()

        text = messages.post_weight_next_step_text(
            weight_text="72.5 кг",
            strava_connect_url="https://example.com/connect",
        )

        self.assertIn("Крок 2 з 2", text)
        self.assertIn("https://example.com/connect", text)

    def test_welcome_text_with_weight_mentions_set_ftp_command(self) -> None:
        messages = _load_messages_module()

        text = messages.onboarding_welcome_text(has_weight=True)

        self.assertIn("/set_ftp", text)
