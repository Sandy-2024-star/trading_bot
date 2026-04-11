"""
Market data caching layer using Redis.
Provides methods to store and retrieve ticker and candlestick data.
"""

import json
from typing import Optional, List, Dict
import pandas as pd
from loguru import logger
from data.redis_manager import redis_manager

class MarketDataCache:
    """Handles caching of market data to reduce API calls and latency."""

    def __init__(self, prefix: str = "market"):
        self.prefix = prefix
        self.redis = redis_manager

    def _get_key(self, category: str, symbol: str, timeframe: Optional[str] = None) -> str:
        """Generate a consistent cache key."""
        if timeframe:
            return f"{self.prefix}:{category}:{symbol}:{timeframe}"
        return f"{self.prefix}:{category}:{symbol}"

    def set_ticker(self, symbol: str, ticker_data: Dict, expire: int = 5):
        """Cache ticker data for a short period."""
        if not self.redis.is_available():
            return

        try:
            key = self._get_key("ticker", symbol)
            self.redis.get_client().setex(key, expire, json.dumps(ticker_data))
        except Exception as e:
            logger.warning(f"Error caching ticker for {symbol}: {e}")

    def get_ticker(self, symbol: str) -> Optional[Dict]:
        """Retrieve cached ticker data."""
        if not self.redis.is_available():
            return None

        try:
            key = self._get_key("ticker", symbol)
            data = self.redis.get_client().get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning(f"Error retrieving cached ticker for {symbol}: {e}")
        return None

    def set_candlesticks(self, symbol: str, timeframe: str, df: pd.DataFrame, expire: int = 300):
        """Cache candlestick data (OHLCV)."""
        if not self.redis.is_available() or df.empty:
            return

        try:
            key = self._get_key("ohlcv", symbol, timeframe)
            # Convert DataFrame to JSON (orient='split' is efficient for storage/retrieval)
            data = df.to_json(orient='split', date_format='iso')
            self.redis.get_client().setex(key, expire, data)
        except Exception as e:
            logger.warning(f"Error caching candlesticks for {symbol} {timeframe}: {e}")

    def get_candlesticks(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """Retrieve cached candlestick data as a DataFrame."""
        if not self.redis.is_available():
            return None

        try:
            key = self._get_key("ohlcv", symbol, timeframe)
            data = self.redis.get_client().get(key)
            if data:
                # Reconstruct DataFrame from JSON
                df = pd.read_json(data, orient='split')
                # Ensure timestamps are correct
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                return df
        except Exception as e:
            logger.warning(f"Error retrieving cached candlesticks for {symbol} {timeframe}: {e}")
        return None

# Global instance
market_cache = MarketDataCache()
