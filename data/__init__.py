"""Data ingestion layer for multi-market trading system."""

try:
    from .alpha_vantage_feed import AlphaVantageFeed
    from .coingecko_feed import CoinGeckoFeed
    from .crypto_feed import CryptoFeed
    from .factory import create_market_data_feed
    from .newsapi_feed import NewsAPIFeed
except ImportError:  # pragma: no cover - fallback for script-style imports
    from data.alpha_vantage_feed import AlphaVantageFeed
    from data.coingecko_feed import CoinGeckoFeed
    from data.crypto_feed import CryptoFeed
    from data.factory import create_market_data_feed
    from data.newsapi_feed import NewsAPIFeed

__all__ = [
    "AlphaVantageFeed",
    "CoinGeckoFeed",
    "CryptoFeed",
    "NewsAPIFeed",
    "create_market_data_feed",
]
