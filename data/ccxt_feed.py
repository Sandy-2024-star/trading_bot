"""
CCXT data feed for cryptocurrency exchanges.
Provides FREE access to 30+ crypto exchanges.
No API keys required for market data (public endpoints).
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

import ccxt
import pandas as pd
from loguru import logger


class CCXTFeed:
    """
    Multi-exchange crypto data provider using CCXT library.
    
    Features:
    - 30+ exchanges (Binance, Coinbase, Kraken, Bybit, etc.)
    - Real-time tickers
    - Orderbook data
    - Historical OHLCV candlesticks
    - Multiple timeframes
    
    Rate Limits:
    - Varies by exchange (typically 1-120 requests/minute)
    - Public endpoints are free
    - Rate limiter included
    
    Supported Exchanges (Free):
    - Binance, Coinbase, Kraken, Bybit, OKX
    - Bitfinex, Gemini, Gate.io, Huobi
    - Kucoin, Bitstamp, Deribit
    """

    DEFAULT_EXCHANGE = "binance"
    
    TIMEFRAME_MAP = {
        "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
        "1h": "1h", "4h": "4h", "1d": "1d", "1w": "1w", "1M": "1M"
    }

    def __init__(
        self,
        exchange_id: str = DEFAULT_EXCHANGE,
        enable_rate_limit: bool = True,
        options: Optional[Dict] = None
    ):
        """
        Initialize CCXT feed.
        
        Args:
            exchange_id: Exchange name (e.g., 'binance', 'coinbase', 'kraken')
            enable_rate_limit: Enable built-in rate limiting
            options: Exchange-specific options
        """
        self.exchange_id = exchange_id
        self.exchange: ccxt.Exchange = getattr(ccxt, exchange_id)({
            "enableRateLimit": enable_rate_limit,
            "options": options or {"defaultType": "spot"}
        })
        self._cache: Dict[str, Dict[str, Any]] = {}
        logger.info(f"CCXTFeed initialized: {exchange_id} (FREE - Public data)")
        logger.info(f"  Supported timeframes: {list(self.TIMEFRAME_MAP.keys())}")

    def symbol_to_ccxt(self, symbol: str) -> str:
        """Convert standard symbol to CCXT format (e.g., BTC/USD)."""
        if "/" in symbol:
            return symbol
        if symbol.endswith("USD"):
            base = symbol[:-3]
            return f"{base}/USD"
        if symbol.endswith("USDT"):
            base = symbol[:-4]
            return f"{base}/USDT"
        if symbol.endswith("INR"):
            base = symbol[:-3]
            return f"{base}/INR"
        return symbol

    def ccxt_to_symbol(self, symbol: str) -> str:
        """Convert CCXT symbol to standard format (e.g., BTCUSD)."""
        return symbol.replace("/", "").replace("-", "")

    async def load_markets(self):
        """Load exchange markets (required before trading)."""
        await asyncio.to_thread(self.exchange.load_markets)
        logger.info(f"Loaded {len(self.exchange.markets)} markets on {self.exchange_id}")

    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch real-time ticker for a symbol.
        
        Args:
            symbol: Trading symbol (e.g., BTCUSD, ETHUSD)
            
        Returns:
            Dict with ticker data
        """
        ccxt_symbol = self.symbol_to_ccxt(symbol)
        
        try:
            ticker = await asyncio.to_thread(
                self.exchange.fetch_ticker,
                ccxt_symbol
            )
            
            return {
                "symbol": symbol.upper(),
                "last_price": ticker.get("last", 0),
                "bid": ticker.get("bid", 0),
                "ask": ticker.get("ask", 0),
                "volume_24h": ticker.get("baseVolume", 0),
                "quote_volume_24h": ticker.get("quoteVolume", 0),
                "high_24h": ticker.get("high", 0),
                "low_24h": ticker.get("low", 0),
                "change_24h": ticker.get("change", 0),
                "change_pct_24h": ticker.get("percentage", 0),
                "timestamp": datetime.fromtimestamp(ticker.get("timestamp", 0) / 1000)
            }
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            return {}

    async def get_orderbook(
        self,
        symbol: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Fetch orderbook snapshot.
        
        Args:
            symbol: Trading symbol
            limit: Number of price levels
            
        Returns:
            Dict with bids and asks
        """
        ccxt_symbol = self.symbol_to_ccxt(symbol)
        
        try:
            orderbook = await asyncio.to_thread(
                self.exchange.fetch_order_book,
                ccxt_symbol,
                limit
            )
            
            return {
                "symbol": symbol.upper(),
                "bids": [[float(p), float(q)] for p, q in orderbook.get("bids", [])[:limit]],
                "asks": [[float(p), float(q)] for p, q in orderbook.get("asks", [])[:limit]],
                "timestamp": datetime.now()
            }
        except Exception as e:
            logger.error(f"Error fetching orderbook for {symbol}: {e}")
            return {}

    async def get_candlesticks(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 100,
        since: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV candlesticks.
        
        Args:
            symbol: Trading symbol
            timeframe: Candle interval (1m, 5m, 15m, 1h, 4h, 1d, 1w)
            limit: Number of candles
            since: Start time in milliseconds
            
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        ccxt_symbol = self.symbol_to_ccxt(symbol)
        tf = self.TIMEFRAME_MAP.get(timeframe, "1h")
        
        try:
            ohlcv = await asyncio.to_thread(
                self.exchange.fetch_ohlcv,
                ccxt_symbol,
                tf,
                since,
                limit
            )
            
            if not ohlcv:
                logger.warning(f"No candlestick data for {symbol}")
                return pd.DataFrame()
            
            df = pd.DataFrame(
                ohlcv,
                columns=["timestamp", "open", "high", "low", "close", "volume"]
            )
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df["symbol"] = symbol.upper()
            
            logger.info(f"Fetched {len(df)} candles for {symbol} ({timeframe}) on {self.exchange_id}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching candlesticks for {symbol}: {e}")
            return pd.DataFrame()

    async def get_multiple_tickers(self, symbols: List[str]) -> List[Dict]:
        """Fetch tickers for multiple symbols concurrently."""
        tasks = [self.get_ticker(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, dict) and r.get("last_price", 0) > 0]

    async def get_available_symbols(self, quote: str = "USDT") -> List[str]:
        """
        Get available trading symbols for a quote currency.
        
        Args:
            quote: Quote currency (e.g., USDT, USD, BTC)
            
        Returns:
            List of trading symbols
        """
        if not self.exchange.markets:
            await self.load_markets()
        
        symbols = [
            self.ccxt_to_symbol(m)
            for m, data in self.exchange.markets.items()
            if data.get("quote") == quote and data.get("active", False)
        ]
        return symbols[:50]

    async def get_exchange_status(self) -> Dict[str, Any]:
        """Get exchange status and API access info."""
        return {
            "exchange": self.exchange_id,
            "rate_limit": self.exchange.enableRateLimit,
            "api_status": "connected",
            "markets_loaded": len(self.exchange.markets) if self.exchange.markets else 0,
            "timeframes": list(self.TIMEFRAME_MAP.keys()),
            "free_tier": True
        }

    def close(self):
        """Close the exchange connection."""
        self._cache.clear()
        logger.info(f"CCXTFeed ({self.exchange_id}) closed")


async def main():
    """Demo usage of CCXTFeed."""
    print("\n" + "="*60)
    print("CCXT FEED DEMO (FREE - Multiple Exchanges)")
    print("="*60)
    
    exchanges_to_test = ["binance", "coinbase", "kraken"]
    
    for exchange_id in exchanges_to_test:
        print(f"\n--- Testing {exchange_id.upper()} ---")
        
        try:
            feed = CCXTFeed(exchange_id=exchange_id)
            
            print(f"[1] Ticker for BTC/USDT:")
            ticker = await feed.get_ticker("BTCUSDT")
            if ticker:
                print(f"  Price: ${ticker['last_price']:,.2f}")
                print(f"  24h Change: {ticker['change_pct_24h']:.2f}%")
                print(f"  Volume: ${ticker['quote_volume_24h']:,.0f}")
            
            print(f"\n[2] Orderbook for ETH/USDT:")
            orderbook = await feed.get_orderbook("ETHUSDT", limit=3)
            if orderbook and orderbook.get("bids"):
                print(f"  Bids: {orderbook['bids'][:3]}")
                print(f"  Asks: {orderbook['asks'][:3]}")
            
            print(f"\n[3] Recent candles for BTC/USDT:")
            candles = await feed.get_candlesticks("BTCUSDT", timeframe="1h", limit=5)
            if not candles.empty:
                print(candles[["timestamp", "close", "volume"]].tail().to_string())
            
            print(f"\n[4] Status:")
            status = await feed.get_exchange_status()
            print(f"  Markets: {status['markets_loaded']}")
            
            feed.close()
            
        except Exception as e:
            print(f"  Error: {e}")
    
    print("\n" + "="*60)
    print("CCXT supports 30+ exchanges - all with FREE market data!")
    print("Exchanges: Binance, Coinbase, Kraken, Bybit, OKX, etc.")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
