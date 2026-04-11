"""
Base class for all market data feeds.
Defines the interface for fetching ticker and candlestick data.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict
import pandas as pd

class MarketDataFeed(ABC):
    """
    Abstract base class for market data providers.
    All data feeds (Crypto, Forex, Indian Markets) should inherit from this.
    """

    @abstractmethod
    async def connect(self):
        """Establish connection to the data provider."""
        pass

    @abstractmethod
    async def close(self):
        """Close the connection to the data provider."""
        pass

    @abstractmethod
    async def get_ticker(self, symbol: str) -> Optional[Dict]:
        """
        Fetch a real-time price snapshot for a symbol.
        
        Returns:
            Dict with keys: symbol, last_price, volume_24h, high_24h, low_24h, timestamp, provider
        """
        pass

    @abstractmethod
    async def get_candlesticks(
        self, 
        symbol: str, 
        timeframe: str = "1h", 
        limit: int = 100
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV candlestick data.
        
        Returns:
            pandas DataFrame with columns: timestamp, open, high, low, close, volume
        """
        pass

    @abstractmethod
    async def get_orderbook(self, symbol: str, depth: int = 10) -> Optional[Dict]:
        """
        Fetch the current orderbook depth.
        
        Returns:
            Dict with keys: symbol, bids (List[List[price, size]]), asks (List[List[price, size]]), timestamp
        """
        pass
