"""
Registry for managing and routing market data feeds.
Routes symbols to the appropriate provider (Crypto, Forex, MT5, etc.).
"""

from typing import Dict, Optional, List
from loguru import logger
from core.base_feed import MarketDataFeed
from data.coingecko_feed import CoinGeckoFeed
from data.crypto_feed import CryptoFeed
from data.forex.oanda_feed import OandaFeed
from data.indian.zerodha_feed import ZerodhaFeed
from data.indian.shoonya_feed import ShoonyaFeed
from data.mt5_feed import MT5Feed
from data.yfinance_feed import YFinanceFeed

try:
    from config.config import config
except ImportError:
    from trading_bot.config.config import config


class MarketRegistry:
    """Routes symbol requests to the correct market data feed."""

    def __init__(self):
        self.feeds: Dict[str, MarketDataFeed] = {}
        self.default_crypto_feed = CoinGeckoFeed()
        self.feeds["crypto"] = self.default_crypto_feed
        self.feeds["forex"] = OandaFeed()
        self.feeds["indian"] = ShoonyaFeed()
        self.feeds["zerodha"] = ZerodhaFeed()
        self.feeds["yfinance"] = YFinanceFeed()

        if config.METAAPI_TOKEN and config.METAAPI_ACCOUNT_ID:
            self.feeds["mt5"] = MT5Feed(config.METAAPI_TOKEN, config.METAAPI_ACCOUNT_ID)
            logger.info("MT5 feed registered in MarketRegistry")

    def register_feed(self, market_type: str, feed: MarketDataFeed):
        """Register a specific feed for a market type."""
        self.feeds[market_type] = feed
        logger.info(f"Registered new feed for market: {market_type}")

    def get_feed_for_symbol(self, symbol: str) -> Optional[MarketDataFeed]:
        """
        Determine which feed to use based on the symbol format.
        """
        upper_symbol = symbol.strip().upper()

        # 1. Indian Markets (Shoonya Priority)
        indian_assets = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "NIFTYBEES"]
        if any(asset in upper_symbol for asset in indian_assets):
            return self.feeds.get("indian") or self.feeds.get("yfinance")

        # 2. Indices (YFinance Priority)
        indices = ["NIFTY", "BANKNIFTY", "AAPL", "MSFT", "TSLA", "IXIC", "DJI", "SPX"]
        if any(asset in upper_symbol for asset in indices):
            return self.feeds.get("yfinance")

        # 3. Forex (OANDA/MT5 Priority)
        forex_currencies = ["EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "NZD"]
        if (
            any(curr in upper_symbol for curr in forex_currencies)
            and len(upper_symbol) <= 7
            and "BTC" not in upper_symbol  # Prevent crypto-FX overlap
        ):
            if "mt5" in self.feeds:
                return self.feeds.get("mt5")
            return self.feeds.get("forex") or self.feeds.get("yfinance")

        # 4. Commodities (MT5 Priority)
        mt5_commodities = ["XAU", "XAG", "XTI", "XBR", "GOLD", "SILVER"]
        if any(curr in upper_symbol for curr in mt5_commodities):
            if "mt5" in self.feeds:
                return self.feeds.get("mt5")
            return self.feeds.get("yfinance")

        # 5. Crypto via Yahoo Finance for live data (faster, real-time)
        crypto_assets = ["BTC", "ETH"]
        if any(upper_symbol.startswith(asset) for asset in crypto_assets):
            return self.feeds.get("yfinance")

        # 6. Other Crypto (CoinGecko Priority)
        other_crypto = [
            "SOL",
            "XRP",
            "ADA",
            "DOGE",
            "BNB",
            "AVAX",
            "MATIC",
            "USDT",
            "USDC",
        ]
        if any(upper_symbol.startswith(asset) for asset in other_crypto):
            return self.feeds.get("crypto")

        # Final Fallback: Yahoo Finance is the most versatile free source
        return self.feeds.get("yfinance") or self.feeds.get("crypto")

    async def close_all(self):
        """Close all registered feeds."""
        for name, feed in self.feeds.items():
            if feed:
                await feed.close()
        logger.info("All market feeds closed")


# Global instance
market_registry = MarketRegistry()
