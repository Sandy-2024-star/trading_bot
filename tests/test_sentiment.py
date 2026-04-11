"""Tests for local-LLM sentiment fallback behavior."""

import unittest
from unittest.mock import patch

from signals.sentiment import SentimentAnalyzer


class SentimentAnalyzerTests(unittest.TestCase):
    """Validate sentiment analyzer routing and fallback."""

    def setUp(self):
        self.articles = [
            {"title": "Bitcoin rally continues after ETF inflows surge"},
            {"title": "Exchange faces investigation after major hack"},
        ]

    @patch("signals.sentiment.config.SENTIMENT_ANALYZER", "local_llm")
    @patch("signals.sentiment.SentimentAnalyzer.LOCAL_CLIENT.is_enabled", return_value=True)
    @patch("signals.sentiment.SentimentAnalyzer.LOCAL_CLIENT.score_sentiment")
    def test_uses_local_llm_when_enabled(self, mock_score_sentiment, _mock_enabled):
        """Prefer the local model when configured."""
        mock_score_sentiment.return_value = {
            "score": 0.4,
            "label": "BULLISH",
            "article_count": 2,
            "analyzer": "local_llm",
            "model": "qwen-coder-3b",
            "reason": "Positive adoption headlines dominate",
        }

        result = SentimentAnalyzer.score_articles(self.articles)

        self.assertEqual(result["analyzer"], "local_llm")
        self.assertEqual(result["model"], "qwen-coder-3b")
        mock_score_sentiment.assert_called_once_with(self.articles)

    @patch("signals.sentiment.config.SENTIMENT_ANALYZER", "local_llm")
    @patch("signals.sentiment.SentimentAnalyzer.LOCAL_CLIENT.is_enabled", return_value=True)
    @patch("signals.sentiment.SentimentAnalyzer.LOCAL_CLIENT.score_sentiment", side_effect=RuntimeError("down"))
    def test_falls_back_to_keywords_when_local_llm_fails(self, _mock_score_sentiment, _mock_enabled):
        """Fallback keeps the system operational when LiteLLM is unavailable."""
        result = SentimentAnalyzer.score_articles(self.articles)

        self.assertEqual(result["analyzer"], "rule_based")
        self.assertEqual(result["article_count"], 2)
        self.assertIn(result["label"], {"BULLISH", "BEARISH", "NEUTRAL"})


if __name__ == "__main__":
    unittest.main()
