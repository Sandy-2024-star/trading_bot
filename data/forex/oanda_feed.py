"""
OANDA market data adapter for Forex trading.
Provides real-time and historical data for currency pairs.
"""

import asyncio
from typing import Optional, List, Dict
import pandas as pd
import httpx
from datetime import datetime
from loguru import logger
from core.base_feed import MarketDataFeed
from data.market_cache import market_cache
from config.config import config

class OandaFeed(MarketDataFeed):
    """
    OANDA API connector for Forex market data.
    """

    def __init__(self, api_key: Optional[str] = None, account_id: Optional[str] = None):
        self.api_key = api_key or config.OANDA_API_KEY
        self.account_id = account_id or config.OANDA_ACCOUNT_ID
        self.base_url = "https://api-fxtrade.oanda.com/v3" if config.OANDA_ENVIRONMENT == "live" else "https://api-fxpractice.oanda.com/v3"
        self.client = httpx.AsyncClient(timeout=10.0)
        self.cache = market_cache
        logger.info(f"OandaFeed initialized (Env: {config.OANDA_ENVIRONMENT})")

    def _normalize_instrument(self, symbol: str) -> str:
        """Map EURUSD -> EUR_USD for OANDA."""
        clean = symbol.strip().upper().replace("/", "_").replace("-", "_")
        if "_" not in clean and len(clean) == 6:
            return f"{clean[:3]}_{clean[3:]}"
        return clean

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def connect(self):
        """Establish connection to OANDA (verify credentials)."""
        if not self.api_key:
            logger.warning("OANDA API key missing. Feed will not be functional.")
            return

        try:
            url = f"{self.base_url}/accounts/{self.account_id}/summary"
            response = await self.client.get(url, headers=self._headers())
            response.raise_for_status()
            logger.info("OANDA connection verified successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to OANDA: {e}")

    async def close(self):
        """Close OANDA client."""
        await self.client.aclose()

    async def get_ticker(self, symbol: str) -> Optional[Dict]:
        """Fetch real-time price snapshot for a forex pair."""
        # Check cache first
        cached = self.cache.get_ticker(symbol)
        if cached:
            logger.debug(f"Cache hit for OANDA ticker: {symbol}")
            return cached

        instrument = self._normalize_instrument(symbol)
        try:
            url = f"{self.base_url}/accounts/{self.account_id}/pricing"
            params = {"instruments": instrument}
            response = await self.client.get(url, headers=self._headers(), params=params)
            response.raise_for_status()
            data = response.json()
            
            if not data.get("prices"):
                return None
                
            price_data = data["prices"][0]
            bid = float(price_data["bids"][0]["price"])
            ask = float(price_data["asks"][0]["price"])
            mid = (bid + ask) / 2
            
            ticker = {
                "symbol": symbol,
                "last_price": mid,
                "bid": bid,
                "ask": ask,
                "timestamp": datetime.fromisoformat(price_data["time"].replace("Z", "+00:00")),
                "provider": "oanda"
            }
            
            # Cache the result (5 second expire)
            self.cache.set_ticker(symbol, ticker, expire=5)
            
            return ticker
        except Exception as e:
            logger.error(f"Error fetching OANDA ticker for {symbol}: {e}")
            return None

    async def get_candlesticks(
        self, 
        symbol: str, 
        timeframe: str = "1h", 
        limit: int = 100
    ) -> pd.DataFrame:
        """Fetch historical OHLCV data from OANDA."""
        # Check cache first
        cached_df = self.cache.get_candlesticks(symbol, timeframe)
        if cached_df is not None and not cached_df.empty:
            logger.debug(f"Cache hit for OANDA candlesticks: {symbol} {timeframe}")
            return cached_df

        instrument = self._normalize_instrument(symbol)
        
        # Map our timeframes to OANDA granularities
        granularity_map = {
            "1m": "M1", "5m": "M5", "15m": "M15", 
            "1h": "H1", "4h": "H4", "1D": "D"
        }
        granularity = granularity_map.get(timeframe, "H1")
        
        try:
            url = f"{self.base_url}/instruments/{instrument}/candles"
            params = {
                "count": limit,
                "granularity": granularity,
                "price": "M"  # Midpoint
            }
            response = await self.client.get(url, headers=self._headers(), params=params)
            response.raise_for_status()
            data = response.json()
            
            candles = []
            for c in data.get("candles", []):
                if not c.get("complete"): continue
                mid = c["mid"]
                candles.append({
                    "timestamp": datetime.fromisoformat(c["time"].replace("Z", "+00:00")),
                    "open": float(mid["o"]),
                    "high": float(mid["h"]),
                    "low": float(mid["l"]),
                    "close": float(mid["c"]),
                    "volume": float(c["volume"])
                })
            
            df = pd.DataFrame(candles)
            if not df.empty:
                df = df.sort_values("timestamp")
                
            # Cache the result (5 minute expire)
            self.cache.set_candlesticks(symbol, timeframe, df, expire=300)
            
            return df
        except Exception as e:
            logger.error(f"Error fetching OANDA candles for {symbol}: {e}")
            return pd.DataFrame()

    async def get_orderbook(self, symbol: str, depth: int = 10) -> Optional[Dict]:
        """OANDA provides order book data via a separate endpoint if needed."""
        return None
