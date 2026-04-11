"""
MT5 market data feed using MetaApi cloud SDK.
Provides access to MT5 market data for Forex, Commodities, and Indices.

Account: Sandesh P
Server: MetaQuotes-Demo
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
from loguru import logger

from core.base_feed import MarketDataFeed


class MT5Feed(MarketDataFeed):
    """
    MT5 data feed via MetaApi cloud.
    
    Supports:
    - Forex: EURUSD, GBPUSD, USDJPY, etc.
    - Commodities: XAUUSD (Gold), XAGUSD (Silver), etc.
    - Indices: US100, US30, GER40, etc.
    
    Rate Limits (Free tier):
    - 500 transactions/month
    """

    TIMEFRAME_MAP = {
        "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
        "1h": "1h", "4h": "4h", "1d": "1d", "1w": "1w"
    }

    def __init__(self, api_token: str = None, account_id: str = None):
        self.api_token = api_token
        self.account_id = account_id
        self._api = None
        self._account = None
        self._connected = False
        logger.info("MT5Feed initialized (MetaApi Cloud)")

    async def connect(self):
        """Connect to MetaApi cloud and MT5 terminal."""
        if self._connected:
            return

        try:
            from metaapi_cloud_sdk import MetaApi
            self._api = MetaApi(token=self.api_token)
            self._account = await self._api.metatrader_account_api.get_account(self.account_id)
            
            if self._account.connection_status != "connected":
                logger.info("Connecting to MT5 terminal via MetaApi...")
                await self._account.connect()
                await self._account.wait_connected(timeout=60)
            
            self._connected = True
            logger.info(f"MT5Feed connected to account {self.account_id}")
            
        except ImportError:
            logger.error("metaapi-python-sdk not installed. Run: pip install metaapi-python-sdk")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to MT5: {e}")
            raise

    async def close(self):
        """Disconnect from MT5 terminal."""
        if self._account and self._connected:
            await self._account.disconnect()
            self._connected = False
            logger.info("MT5Feed disconnected")

    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch real-time ticker data for a symbol.
        
        Args:
            symbol: Trading symbol (e.g., EURUSD, XAUUSD)
            
        Returns:
            Dict with keys: symbol, last_price, bid, ask, volume_24h, timestamp
        """
        if not self._connected:
            await self.connect()

        try:
            price = await self._account.get_symbol_price(symbol)
            
            return {
                "symbol": symbol.upper(),
                "last_price": (price.bid + price.ask) / 2 if price else 0,
                "bid": price.bid if price else 0,
                "ask": price.ask if price else 0,
                "volume_24h": getattr(price, 'volume', 0) or 0,
                "high_24h": getattr(price, 'high', 0) or 0,
                "low_24h": getattr(price, 'low', 0) or 0,
                "timestamp": datetime.now()
            }
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            return {}

    async def get_candlesticks(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 100
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV candlestick data.
        
        Args:
            symbol: Trading symbol
            timeframe: Candle interval (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Number of candles
            
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        if not self._connected:
            await self.connect()

        tf = self.TIMEFRAME_MAP.get(timeframe, "1h")
        
        try:
            candles = await self._account.get_historical_candles(
                symbol=symbol,
                timeframe=tf,
                limit=limit
            )
            
            if not candles:
                logger.warning(f"No candlestick data for {symbol}")
                return pd.DataFrame()

            data = []
            for c in candles:
                data.append({
                    "timestamp": datetime.fromtimestamp(c.time / 1000),
                    "open": c.open,
                    "high": c.high,
                    "low": c.low,
                    "close": c.close,
                    "volume": getattr(c, 'tick_volume', 0) or 0
                })

            df = pd.DataFrame(data)
            df["symbol"] = symbol.upper()
            
            logger.info(f"Fetched {len(df)} candles for {symbol} ({timeframe})")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching candlesticks for {symbol}: {e}")
            return pd.DataFrame()

    async def get_orderbook(self, symbol: str, depth: int = 10) -> Dict[str, Any]:
        """
        Fetch orderbook snapshot.
        
        Args:
            symbol: Trading symbol
            depth: Number of price levels
            
        Returns:
            Dict with keys: symbol, bids, asks, timestamp
        """
        if not self._connected:
            await self.connect()

        try:
            orderbook = await self._account.get_book(symbol)
            
            if not orderbook:
                return {}

            bids = [[orderbook.bids[i].price, orderbook.bids[i].volume] 
                    for i in range(min(depth, len(orderbook.bids)))]
            asks = [[orderbook.asks[i].price, orderbook.asks[i].volume] 
                    for i in range(min(depth, len(orderbook.asks)))]

            return {
                "symbol": symbol.upper(),
                "bids": bids,
                "asks": asks,
                "timestamp": datetime.now()
            }
        except Exception as e:
            logger.error(f"Error fetching orderbook for {symbol}: {e}")
            return {}

    async def get_multiple_tickers(self, symbols: List[str]) -> List[Dict]:
        """Fetch ticker data for multiple symbols concurrently."""
        if not self._connected:
            await self.connect()
            
        tasks = [self.get_ticker(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, dict) and r.get("last_price", 0) > 0]

    async def get_symbol_specification(self, symbol: str) -> Dict[str, Any]:
        """Get symbol specification (lot size, spread, etc.)."""
        if not self._connected:
            await self.connect()

        try:
            spec = await self._account.get_symbol_specification(symbol)
            return {
                "symbol": symbol,
                "description": getattr(spec, 'description', ''),
                "lot_size": getattr(spec, 'lot_size', 1),
                "tick_size": getattr(spec, 'tick_size', 0.00001),
                "min_lot": getattr(spec, 'min_lot', 0.01),
                "max_lot": getattr(spec, 'max_lot', 100),
                "spread": getattr(spec, 'spread', 0),
            }
        except Exception as e:
            logger.error(f"Error fetching specification for {symbol}: {e}")
            return {}

    def get_account_info(self) -> Dict[str, Any]:
        """Get MT5 account information."""
        if not self._account:
            return {}
        
        try:
            info = self._account.account_information
            return {
                "name": getattr(info, 'name', ''),
                "server": getattr(info, 'server', ''),
                "currency": getattr(info, 'currency', ''),
                "balance": getattr(info, 'balance', 0),
                "equity": getattr(info, 'equity', 0),
                "margin": getattr(info, 'margin', 0),
                "free_margin": getattr(info, 'margin_free', 0),
                "leverage": getattr(info, 'leverage', 1),
            }
        except Exception as e:
            logger.error(f"Error fetching account info: {e}")
            return {}


async def main():
    """Demo usage of MT5Feed."""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_token = os.getenv("METAAPI_TOKEN")
    account_id = os.getenv("METAAPI_ACCOUNT_ID")
    
    if not api_token or not account_id:
        print("\n⚠️  Configure METAAPI_TOKEN and METAAPI_ACCOUNT_ID in config/.env")
        print("   See: trading_bot/MT5_SETUP_QUICKREF.md")
        return

    print("\n" + "="*60)
    print("MT5 FEED DEMO (MetaApi Cloud)")
    print("="*60)

    feed = MT5Feed(api_token, account_id)

    try:
        await feed.connect()

        print("\n[1] Account Info:")
        info = feed.get_account_info()
        if info:
            print(f"  Balance: ${info.get('balance', 0):,.2f}")
            print(f"  Equity: ${info.get('equity', 0):,.2f}")
            print(f"  Server: {info.get('server', 'N/A')}")

        print("\n[2] Forex Tickers:")
        for symbol in ["EURUSD", "GBPUSD", "USDJPY"]:
            ticker = await feed.get_ticker(symbol)
            if ticker:
                print(f"  {symbol}: Bid={ticker['bid']:.5f}, Ask={ticker['ask']:.5f}")

        print("\n[3] Commodities:")
        for symbol in ["XAUUSD", "XAGUSD"]:
            ticker = await feed.get_ticker(symbol)
            if ticker:
                print(f"  {symbol}: ${ticker['last_price']:.2f}")

        print("\n[4] Indices:")
        for symbol in ["US100", "US30"]:
            ticker = await feed.get_ticker(symbol)
            if ticker:
                print(f"  {symbol}: {ticker['last_price']:.2f}")

        print("\n[5] Historical Candles (EURUSD, H1):")
        candles = await feed.get_candlesticks("EURUSD", timeframe="1h", limit=5)
        if not candles.empty:
            print(candles[["timestamp", "close"]].to_string())

    finally:
        await feed.close()

    print("\n" + "="*60)
    print("MT5Feed ready for trading!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
