"""
Simple rule-based sentiment scoring for market news articles.
"""

from typing import Dict, List

from loguru import logger

try:
    from ai.local_llm import LocalLLMClient
    from config.config import config
except ImportError:  # pragma: no cover - fallback for package imports
    from trading_bot.ai.local_llm import LocalLLMClient
    from trading_bot.config.config import config


class SentimentAnalyzer:
    """
    Lightweight sentiment scorer for article headlines and summaries.
    """

    POSITIVE_KEYWORDS = {
        "beat", "bullish", "buy", "gain", "growth", "launch", "partnership",
        "rally", "record", "recovery", "surge", "upgrade", "adoption",
    }
    NEGATIVE_KEYWORDS = {
        "ban", "bearish", "crash", "decline", "downgrade", "drop", "fraud",
        "hack", "investigation", "lawsuit", "loss", "miss", "risk", "sell",
    }
    LOCAL_CLIENT = LocalLLMClient()

    @classmethod
    def score_articles(cls, articles: List[Dict]) -> Dict:
        """
        Score a collection of article dicts and return a summary.
        """
        if not articles:
            return {
                "score": 0.0,
                "label": "NEUTRAL",
                "article_count": 0,
                "analyzer": "rule_based",
                "model": None,
                "reason": "No articles available",
            }

        analyzer_mode = config.SENTIMENT_ANALYZER
        use_local_llm = analyzer_mode == "local_llm" or (
            analyzer_mode == "auto" and cls.LOCAL_CLIENT.is_enabled()
        )

        if use_local_llm and cls.LOCAL_CLIENT.is_enabled():
            try:
                return cls.LOCAL_CLIENT.score_sentiment(articles)
            except Exception as exc:
                logger.warning(
                    "Local LLM sentiment failed, falling back to keyword analyzer: {}",
                    exc,
                )

        return cls._score_with_keywords(articles)

    @classmethod
    def _score_with_keywords(cls, articles: List[Dict]) -> Dict:
        """Score articles using the built-in keyword heuristic."""
        scores = []
        for article in articles:
            text = " ".join(
                str(article.get(field, ""))
                for field in ("title", "description", "content", "summary")
            ).lower()

            positive_hits = sum(1 for keyword in cls.POSITIVE_KEYWORDS if keyword in text)
            negative_hits = sum(1 for keyword in cls.NEGATIVE_KEYWORDS if keyword in text)
            total_hits = positive_hits + negative_hits

            if total_hits == 0:
                scores.append(0.0)
            else:
                scores.append((positive_hits - negative_hits) / total_hits)

        average_score = sum(scores) / len(scores)

        if average_score >= 0.25:
            label = "BULLISH"
        elif average_score <= -0.25:
            label = "BEARISH"
        else:
            label = "NEUTRAL"

        logger.info(
            "Scored {} articles with sentiment {} ({:.2f})",
            len(articles),
            label,
            average_score,
        )
        return {
            "score": average_score,
            "label": label,
            "article_count": len(articles),
            "analyzer": "rule_based",
            "model": None,
            "reason": "Keyword hit balance from article text",
        }
