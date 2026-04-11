"""
NewsAPI adapter for development-time article retrieval.
"""

from datetime import date
from typing import Dict, List, Optional

import httpx
from loguru import logger

try:
    from config.config import config
except ImportError:  # pragma: no cover - fallback for package imports
    from trading_bot.config.config import config


class NewsAPIFeed:
    """
    NewsAPI adapter for article search.
    """

    BASE_URL = "https://newsapi.org/v2"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.NEWS_API_KEY
        self.client = httpx.AsyncClient(timeout=30.0)
        logger.info("NewsAPIFeed initialized")

    async def close(self):
        """Close HTTP client connection."""
        await self.client.aclose()

    async def search_everything(
        self,
        query: str,
        from_date: Optional[date] = None,
        language: str = "en",
        sort_by: str = "publishedAt",
        page_size: int = 20,
    ) -> List[Dict]:
        """
        Search the NewsAPI `/everything` endpoint.
        """
        if not self.api_key:
            logger.error("NEWS_API_KEY is not configured")
            return []

        try:
            params = {
                "q": query,
                "language": language,
                "sortBy": sort_by,
                "pageSize": page_size,
                "apiKey": self.api_key,
            }
            if from_date:
                params["from"] = from_date.isoformat()

            response = await self.client.get(f"{self.BASE_URL}/everything", params=params)
            response.raise_for_status()
            payload = response.json()

            if payload.get("status") != "ok":
                logger.error(f"NewsAPI error: {payload}")
                return []

            return payload.get("articles", [])
        except Exception as exc:
            logger.error(f"Error fetching NewsAPI articles for query '{query}': {exc}")
            return []

    async def search_market_news(
        self,
        query: str = "bitcoin OR forex OR stocks",
        page_size: int = 20,
    ) -> List[Dict]:
        """
        Convenience wrapper for broad market-news retrieval.
        """
        return await self.search_everything(query=query, page_size=page_size)
