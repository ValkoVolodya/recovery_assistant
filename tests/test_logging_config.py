import importlib
import logging
import sys
import unittest


class LoggingConfigTests(unittest.TestCase):
    def test_configure_logging_sets_info_level_on_root(self) -> None:
        sys.modules.pop("app.logging_config", None)
        module = importlib.import_module("app.logging_config")

        logging.getLogger().handlers.clear()
        logging.getLogger().setLevel(logging.WARNING)

        module.configure_logging()

        self.assertEqual(logging.getLogger().level, logging.INFO)
        self.assertTrue(logging.getLogger().handlers)
