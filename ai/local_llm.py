"""
Small OpenAI-compatible client for local LiteLLM/Ollama sentiment prompts.
"""

import json
from typing import Dict, List, Optional

import requests
from loguru import logger

try:
    from config.config import config
except ImportError:  # pragma: no cover - fallback for package imports
    from trading_bot.config.config import config


class LocalLLMClient:
    """Thin client for calling a local LiteLLM endpoint."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        endpoint: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        temperature: Optional[float] = None,
        api_key: Optional[str] = None,
    ):
        self.base_url = (base_url or config.LOCAL_LLM_BASE_URL).rstrip("/")
        endpoint = endpoint or config.LOCAL_LLM_ENDPOINT
        self.endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        self.model = model or config.LOCAL_LLM_MODEL
        self.timeout_seconds = timeout_seconds or config.LOCAL_LLM_TIMEOUT_SECONDS
        self.temperature = (
            config.LOCAL_LLM_TEMPERATURE if temperature is None else temperature
        )
        self.api_key = api_key if api_key is not None else config.LOCAL_LLM_API_KEY

    @property
    def url(self) -> str:
        """Resolved chat completion URL."""
        return f"{self.base_url}{self.endpoint}"

    def is_enabled(self) -> bool:
        """Return True when the local client is configured for use."""
        return bool(config.LOCAL_LLM_ENABLED and self.model and self.base_url)

    def score_sentiment(self, articles: List[Dict]) -> Dict:
        """
        Ask the local model for a coarse market sentiment score.

        Returns a dict with score, label, article_count, analyzer, model, and reason.
        Raises requests/JSON errors on transport or parsing failures.
        """
        if not articles:
            return {
                "score": 0.0,
                "label": "NEUTRAL",
                "article_count": 0,
                "analyzer": "local_llm",
                "model": self.model,
                "reason": "No articles available",
            }

        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a market sentiment classifier. "
                        "Read the supplied article headlines and summaries, then return "
                        "strict JSON with keys score, label, and reason. "
                        "score must be a number between -1 and 1. "
                        "label must be one of BULLISH, BEARISH, or NEUTRAL. "
                        "reason must be short and mention the main drivers."
                    ),
                },
                {
                    "role": "user",
                    "content": self._build_prompt(articles),
                },
            ],
        }

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        response = requests.post(
            self.url,
            headers=headers,
            json=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()

        data = response.json()
        content = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        parsed = self._parse_json_object(content)
        score = max(-1.0, min(1.0, float(parsed.get("score", 0.0))))
        label = str(parsed.get("label", "NEUTRAL")).upper()
        if label not in {"BULLISH", "BEARISH", "NEUTRAL"}:
            label = "NEUTRAL"

        result = {
            "score": score,
            "label": label,
            "article_count": len(articles),
            "analyzer": "local_llm",
            "model": self.model,
            "reason": str(parsed.get("reason", "")).strip(),
        }
        logger.info(
            "Local LLM sentiment scored {} articles with {} ({:.2f}) via {}",
            len(articles),
            result["label"],
            result["score"],
            self.model,
        )
        return result

    def _build_prompt(self, articles: List[Dict]) -> str:
        """Build a concise prompt body from market news articles."""
        lines = []
        for index, article in enumerate(articles[:12], start=1):
            title = str(article.get("title", "")).strip()
            description = str(article.get("description", "")).strip()
            summary = str(article.get("summary", "")).strip()
            parts = [part for part in (title, description or summary) if part]
            if parts:
                lines.append(f"{index}. {' | '.join(parts)}")

        if not lines:
            lines.append("1. No article text provided.")

        return (
            "Classify the overall short-term market sentiment from these articles.\n"
            "Treat crypto and macro headlines as market-moving context.\n"
            "Return only JSON.\n\n"
            + "\n".join(lines)
        )

    @staticmethod
    def _parse_json_object(text: str) -> Dict:
        """Extract the first JSON object from a model response."""
        cleaned = text.strip()
        if cleaned.startswith("{") and cleaned.endswith("}"):
            return json.loads(cleaned)

        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise json.JSONDecodeError("No JSON object found", cleaned, 0)
        return json.loads(cleaned[start:end + 1])
