"""
Alpha Vantage adapter for free forex and news sentiment access.
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import httpx
import pandas as pd
from loguru import logger

try:
    from config.config import config
except ImportError:  # pragma: no cover - fallback for package imports
    from trading_bot.config.config import config


class AlphaVantageFeed:
    """
    Alpha Vantage adapter for FX market data and market news sentiment.
    """

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.ALPHA_VANTAGE_API_KEY
        self.client = httpx.AsyncClient(timeout=30.0)
        self._last_request_at = 0.0
        logger.info("AlphaVantageFeed initialized")

    async def close(self):
        """Close HTTP client connection."""
        await self.client.aclose()

    def _split_pair(self, symbol: str) -> Tuple[str, str]:
        clean_symbol = symbol.strip().upper().replace("-", "/").replace("_", "/")
        if "/" in clean_symbol:
            base, quote = clean_symbol.split("/", 1)
            return base, quote
        if len(clean_symbol) == 6:
            return clean_symbol[:3], clean_symbol[3:]
        raise ValueError(f"Unsupported FX symbol format: {symbol}")

    async def _query(self, params: Dict[str, str]) -> Dict:
        if not self.api_key:
            logger.error("ALPHA_VANTAGE_API_KEY is not configured")
            return {}

        for attempt in range(2):
            elapsed = time.monotonic() - self._last_request_at
            if elapsed < 1.2:
                await asyncio.sleep(1.2 - elapsed)

            response = await self.client.get(self.BASE_URL, params={**params, "apikey": self.api_key})
            self._last_request_at = time.monotonic()
            response.raise_for_status()
            data = response.json()

            if "Error Message" in data:
                logger.error(f"Alpha Vantage error: {data['Error Message']}")
                return {}
            if "Information" in data or "Note" in data:
                message = data.get("Information") or data.get("Note")
                logger.warning(f"Alpha Vantage info: {message}")
                if attempt == 0:
                    await asyncio.sleep(1.5)
                    continue
                return {}

            return data

        return {}

    async def get_exchange_rate(self, symbol: str = "EUR/USD") -> Dict:
        """
        Fetch the latest FX conversion rate.
        """
        try:
            from_symbol, to_symbol = self._split_pair(symbol)
            data = await self._query(
                {
                    "function": "CURRENCY_EXCHANGE_RATE",
                    "from_currency": from_symbol,
                    "to_currency": to_symbol,
                }
            )

            result = data.get("Realtime Currency Exchange Rate", {})
            if not result:
                return {}

            return {
                "symbol": f"{from_symbol}/{to_symbol}",
                "exchange_rate": float(result.get("5. Exchange Rate", 0)),
                "bid": float(result.get("8. Bid Price", 0) or 0),
                "ask": float(result.get("9. Ask Price", 0) or 0),
                "timestamp": datetime.now(),
            }
        except Exception as exc:
            logger.error(f"Error fetching Alpha Vantage FX rate for {symbol}: {exc}")
            return {}

    async def get_candlesticks(
        self,
        symbol: str = "EUR/USD",
        timeframe: str = "1D",
        limit: int = 100,
    ) -> pd.DataFrame:
        """
        Fetch FX candlestick data.
        """
        try:
            from_symbol, to_symbol = self._split_pair(symbol)
            interval_map = {
                "1m": "1min",
                "5m": "5min",
                "15m": "15min",
                "30m": "30min",
                "1h": "60min",
            }

            if timeframe == "1D":
                data = await self._query(
                    {
                        "function": "FX_DAILY",
                        "from_symbol": from_symbol,
                        "to_symbol": to_symbol,
                        "outputsize": "compact",
                    }
                )
                series_key = "Time Series FX (Daily)"
            else:
                interval = interval_map.get(timeframe)
                if not interval:
                    logger.error(f"Unsupported Alpha Vantage timeframe: {timeframe}")
                    return pd.DataFrame()

                data = await self._query(
                    {
                        "function": "FX_INTRADAY",
                        "from_symbol": from_symbol,
                        "to_symbol": to_symbol,
                        "interval": interval,
                        "outputsize": "compact",
                    }
                )
                series_key = f"Time Series FX ({interval})"

            series = data.get(series_key, {})
            if not series:
                return pd.DataFrame()

            rows = []
            for timestamp, values in series.items():
                rows.append(
                    {
                        "timestamp": pd.to_datetime(timestamp),
                        "open": float(values["1. open"]),
                        "high": float(values["2. high"]),
                        "low": float(values["3. low"]),
                        "close": float(values["4. close"]),
                        "volume": 0.0,
                    }
                )

            df = pd.DataFrame(rows).sort_values("timestamp").tail(limit).reset_index(drop=True)
            logger.info(f"Fetched {len(df)} Alpha Vantage candles for {symbol}")
            return df
        except Exception as exc:
            logger.error(f"Error fetching Alpha Vantage candles for {symbol}: {exc}")
            return pd.DataFrame()

    async def get_news_sentiment(
        self,
        tickers: Optional[List[str]] = None,
        topics: Optional[List[str]] = None,
        limit: int = 20,
    ) -> List[Dict]:
        """
        Fetch market news and sentiment entries.
        """
        try:
            params = {
                "function": "NEWS_SENTIMENT",
                "sort": "LATEST",
                "limit": str(limit),
            }
            if tickers:
                params["tickers"] = ",".join(tickers)
            if topics:
                params["topics"] = ",".join(topics)

            data = await self._query(params)
            return data.get("feed", [])
        except Exception as exc:
            logger.error(f"Error fetching Alpha Vantage news sentiment: {exc}")
            return []
