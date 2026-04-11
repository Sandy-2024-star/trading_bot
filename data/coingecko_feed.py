"""
CoinGecko market data adapter for free crypto price and chart data.
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple

import httpx
import pandas as pd
from loguru import logger
from data.market_cache import market_cache
from core.base_feed import MarketDataFeed

try:
    from config.config import config
except ImportError:  # pragma: no cover - fallback for package imports
    from trading_bot.config.config import config


class CoinGeckoFeed(MarketDataFeed):
    """
    CoinGecko adapter focused on free market data endpoints.

    Supports:
    - Spot price snapshots
    - Historical OHLC candles
    """

    BASE_URL = "https://api.coingecko.com/api/v3"
    SYMBOL_TO_ID = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
        "XRP": "ripple",
        "DOGE": "dogecoin",
        "ADA": "cardano",
        "BNB": "binancecoin",
        "AVAX": "avalanche-2",
        "MATIC": "matic-network",
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.COINGECKO_API_KEY
        self.client = httpx.AsyncClient(timeout=30.0)
        self.cache = market_cache
        logger.info("CoinGeckoFeed initialized")

    async def connect(self):
        """Establish connection (no-op for REST)."""
        pass

    async def close(self):
        """Close HTTP client connection."""
        await self.client.aclose()

    def _headers(self) -> Dict[str, str]:
        headers = {}
        if self.api_key:
            headers["x-cg-demo-api-key"] = self.api_key
        return headers

    def _split_symbol(self, symbol: str) -> Tuple[str, str]:
        clean_symbol = symbol.strip().upper().replace("-", "/").replace("_", "/")
        if "/" in clean_symbol:
            base, quote = clean_symbol.split("/", 1)
            return base, quote

        quote_candidates = ("USDT", "USDC", "USD", "EUR", "INR", "BTC", "ETH")
        for quote in quote_candidates:
            if clean_symbol.endswith(quote) and len(clean_symbol) > len(quote):
                return clean_symbol[:-len(quote)], quote

        return clean_symbol, "USD"

    def _resolve_coin_id(self, base_symbol: str) -> str:
        return self.SYMBOL_TO_ID.get(base_symbol, base_symbol.lower())

    def _days_for_timeframe(self, timeframe: str) -> str:
        return {
            "1m": "1",
            "5m": "1",
            "15m": "1",
            "1h": "7",
            "4h": "30",
            "1D": "90",
        }.get(timeframe, "30")

    async def get_ticker(self, symbol: str = "BTCUSD") -> Dict:
        """
        Fetch a spot price snapshot.

        Args:
            symbol: Trading pair such as BTCUSD or ETH/USD.

        Returns:
            Dict with normalized ticker fields.
        """
        # Check cache first
        cached = self.cache.get_ticker(symbol)
        if cached:
            logger.debug(f"Cache hit for ticker: {symbol}")
            return cached

        try:
            base, quote = self._split_symbol(symbol)
            coin_id = self._resolve_coin_id(base)
            response = await self.client.get(
                f"{self.BASE_URL}/simple/price",
                params={
                    "ids": coin_id,
                    "vs_currencies": quote.lower(),
                    "include_market_cap": "true",
                    "include_24hr_vol": "true",
                    "include_24hr_change": "true",
                    "include_last_updated_at": "true",
                },
                headers=self._headers(),
            )
            response.raise_for_status()
            data = response.json().get(coin_id, {})

            if not data or quote.lower() not in data:
                logger.error(f"CoinGecko returned no price data for {symbol}")
                return {}

            updated_at = data.get("last_updated_at")
            ticker = {
                "symbol": symbol,
                "last_price": float(data.get(quote.lower(), 0)),
                "volume_24h": float(data.get(f"{quote.lower()}_24h_vol", 0) or 0),
                "change_24h": float(data.get(f"{quote.lower()}_24h_change", 0) or 0),
                "market_cap": float(data.get(f"{quote.lower()}_market_cap", 0) or 0),
                "timestamp": datetime.fromtimestamp(updated_at) if updated_at else datetime.now(),
            }
            
            # Cache the result (5 second expire)
            self.cache.set_ticker(symbol, ticker, expire=5)
            
            return ticker
        except Exception as exc:
            logger.error(f"Error fetching CoinGecko ticker for {symbol}: {exc}")
            return {}

    async def get_orderbook(self, symbol: str = "BTCUSD", depth: int = 10) -> Dict:
        """
        CoinGecko does not expose a public orderbook endpoint.
        """
        logger.warning(
            "Orderbook data is not available from CoinGecko for {}. Requested depth {} ignored.",
            symbol,
            depth,
        )
        return {}

    async def get_candlesticks(
        self,
        symbol: str = "BTCUSD",
        timeframe: str = "1h",
        limit: int = 100,
    ) -> pd.DataFrame:
        """
        Fetch historical OHLC candles.

        Args:
            symbol: Trading pair such as BTCUSD or ETH/USD.
            timeframe: Desired bar interval. Used to pick a practical lookback window.
            limit: Maximum number of candles returned.

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        # Check cache first
        cached_df = self.cache.get_candlesticks(symbol, timeframe)
        if cached_df is not None and not cached_df.empty:
            logger.debug(f"Cache hit for candlesticks: {symbol} {timeframe}")
            return cached_df

        try:
            base, quote = self._split_symbol(symbol)
            coin_id = self._resolve_coin_id(base)
            response = await self.client.get(
                f"{self.BASE_URL}/coins/{coin_id}/ohlc",
                params={
                    "vs_currency": quote.lower(),
                    "days": self._days_for_timeframe(timeframe),
                },
                headers=self._headers(),
            )
            response.raise_for_status()
            rows: List[List[float]] = response.json()

            if not rows:
                logger.warning(f"No CoinGecko candles returned for {symbol}")
                return pd.DataFrame()

            df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            for column in ("open", "high", "low", "close"):
                df[column] = df[column].astype(float)

            df["volume"] = 0.0
            df = df.sort_values("timestamp").tail(limit).reset_index(drop=True)
            
            # Cache the result (5 minute expire)
            self.cache.set_candlesticks(symbol, timeframe, df, expire=300)
            
            logger.info(f"Fetched {len(df)} CoinGecko candles for {symbol}")
            return df
        except Exception as exc:
            logger.error(f"Error fetching CoinGecko candles for {symbol}: {exc}")
            return pd.DataFrame()

    async def get_multiple_tickers(self, symbols: List[str]) -> List[Dict]:
        """
        Fetch multiple CoinGecko spot price snapshots sequentially.
        """
        results = []
        for symbol in symbols:
            ticker = await self.get_ticker(symbol)
            if ticker:
                results.append(ticker)
        return results
