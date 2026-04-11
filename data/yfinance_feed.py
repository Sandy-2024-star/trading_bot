"""
Yahoo Finance market data adapter for free global stocks, indices, and forex.
"""

import asyncio
from typing import Optional, List, Dict
import pandas as pd
import yfinance as yf
from datetime import datetime
from loguru import logger
from core.base_feed import MarketDataFeed
from data.market_cache import market_cache

class YFinanceFeed(MarketDataFeed):
    """
    Yahoo Finance API connector.
    Provides free real-time and historical data via yfinance.
    """

    def __init__(self):
        self.cache = market_cache
        logger.info("YFinanceFeed initialized")

    def _normalize_symbol(self, symbol: str) -> str:
        """Map common symbols to Yahoo Finance format."""
        upper = symbol.strip().upper()
        
        # Mapping table
        mapping = {
            "BTCUSD": "BTC-USD",
            "ETHUSD": "ETH-USD",
            "EURUSD": "EURUSD=X",
            "GBPUSD": "GBPUSD=X",
            "RELIANCE": "RELIANCE.NS",
            "NIFTY50": "^NSEI",
            "GOLD": "GC=F",
            "SILVER": "SI=F"
        }
        
        return mapping.get(upper, upper)

    async def connect(self):
        """No-op for Yahoo Finance."""
        pass

    async def close(self):
        """No-op for Yahoo Finance."""
        pass

    async def get_ticker(self, symbol: str) -> Optional[Dict]:
        """Fetch a spot price snapshot."""
        # Check cache
        cached = self.cache.get_ticker(symbol)
        if cached:
            return cached

        yf_symbol = self._normalize_symbol(symbol)
        try:
            # yfinance calls are blocking, so wrap in run_in_executor
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(None, lambda: yf.Ticker(yf_symbol))
            info = await loop.run_in_executor(None, lambda: ticker.fast_info)
            
            data = {
                "symbol": symbol,
                "last_price": float(info['last_price']),
                "volume_24h": float(info.get('last_volume', 0)),
                "high_24h": float(info.get('day_high', 0)),
                "low_24h": float(info.get('day_low', 0)),
                "timestamp": datetime.now(),
                "provider": "yfinance"
            }
            
            self.cache.set_ticker(symbol, data, expire=10)
            return data
        except Exception as e:
            logger.error(f"Error fetching YFinance ticker for {symbol}: {e}")
            return None

    async def get_candlesticks(
        self, 
        symbol: str, 
        timeframe: str = "1h", 
        limit: int = 100
    ) -> pd.DataFrame:
        """Fetch historical OHLCV data."""
        # Check cache
        cached_df = self.cache.get_candlesticks(symbol, timeframe)
        if cached_df is not None and not cached_df.empty:
            return cached_df

        yf_symbol = self._normalize_symbol(symbol)
        
        # Map timeframes to Yahoo intervals
        interval_map = {
            "1m": "1m", "5m": "5m", "15m": "15m", 
            "1h": "1h", "1D": "1d", "1W": "1wk"
        }
        interval = interval_map.get(timeframe, "1h")
        
        # Determine period based on limit and interval
        period = "5d" # default
        if timeframe == "1h" and limit > 100: period = "1mo"
        if timeframe == "1D": period = "1y"

        try:
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None, 
                lambda: yf.download(yf_symbol, period=period, interval=interval, progress=False)
            )
            
            if df.empty:
                return pd.DataFrame()
                
            # Handle MultiIndex columns (new in yfinance)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # Normalize column names
            df.columns = [c.lower() for c in df.columns]
            df = df.reset_index()
            df.columns = [c.lower() for c in df.columns]
            
            # Map Yahoo's index name or columns to our 'timestamp'
            if 'date' in df.columns:
                df = df.rename(columns={'date': 'timestamp'})
            elif 'datetime' in df.columns:
                df = df.rename(columns={'datetime': 'timestamp'})
            
            # Filter and take tail
            required_cols = ['timestamp', 'open', 'high', 'low', 'close']
            if 'volume' in df.columns:
                required_cols.append('volume')
            else:
                df['volume'] = 0.0
                required_cols.append('volume')
                
            df = df[required_cols]
            df = df.tail(limit).sort_values("timestamp")
            
            # Ensure types are correct for JSON serialization later
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            self.cache.set_candlesticks(symbol, timeframe, df, expire=300)
            return df
        except Exception as e:
            logger.error(f"Error fetching YFinance candles for {symbol}: {e}")
            return pd.DataFrame()

    async def get_orderbook(self, symbol: str, depth: int = 10) -> Optional[Dict]:
        """Yahoo Finance does not provide real-time order books."""
        return None
