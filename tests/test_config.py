"""Tests for local LLM config validation."""

import unittest

from config.config import Config


class ConfigValidationTests(unittest.TestCase):
    """Validate non-secret configuration rules."""

    def test_known_sentiment_analyzer_is_valid(self):
        original = Config.SENTIMENT_ANALYZER
        try:
            Config.SENTIMENT_ANALYZER = "local_llm"
            self.assertTrue(Config.validate())
        finally:
            Config.SENTIMENT_ANALYZER = original

    def test_invalid_sentiment_analyzer_fails_validation(self):
        original = Config.SENTIMENT_ANALYZER
        try:
            Config.SENTIMENT_ANALYZER = "unsupported"
            self.assertFalse(Config.validate())
        finally:
            Config.SENTIMENT_ANALYZER = original


if __name__ == "__main__":
    unittest.main()
