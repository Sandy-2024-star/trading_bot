"""
Factories for selecting configured data providers.
"""

from loguru import logger

try:
    from config.config import config
    from data.coingecko_feed import CoinGeckoFeed
    from data.crypto_feed import CryptoFeed
    from data.yfinance_feed import YFinanceFeed
    from data.mt5_feed import MT5Feed
except ImportError:  # pragma: no cover - fallback for package imports
    from trading_bot.config.config import config
    from trading_bot.data.coingecko_feed import CoinGeckoFeed
    from trading_bot.data.crypto_feed import CryptoFeed
    from trading_bot.data.yfinance_feed import YFinanceFeed
    from trading_bot.data.mt5_feed import MT5Feed


def create_market_data_feed(provider: str = None):
    """
    Create the configured market data feed.

    Supported providers:
    - crypto_com: Crypto.com exchange
    - coingecko: CoinGecko API
    - yfinance: Yahoo Finance (FREE - stocks, forex, crypto)
    - mt5: MetaTrader 5 via MetaApi (forex, commodities, indices)
    """
    selected_provider = (provider or config.MARKET_DATA_PROVIDER).lower()

    if selected_provider == "crypto_com":
        logger.info("Using Crypto.com as market data provider")
        return CryptoFeed()
    if selected_provider == "coingecko":
        logger.info("Using CoinGecko as market data provider")
        return CoinGeckoFeed()
    if selected_provider == "yfinance":
        logger.info("Using Yahoo Finance as market data provider (FREE)")
        return YFinanceFeed()
    if selected_provider == "mt5":
        logger.info("Using MT5 (MetaApi) as market data provider")
        if not config.METAAPI_TOKEN or not config.METAAPI_ACCOUNT_ID:
            raise ValueError("METAAPI_TOKEN and METAAPI_ACCOUNT_ID must be configured")
        return MT5Feed(config.METAAPI_TOKEN, config.METAAPI_ACCOUNT_ID)

    raise ValueError(f"Unsupported market data provider: {selected_provider}")


def create_mt5_feed():
    """Create MT5 data feed with config credentials."""
    if not config.METAAPI_TOKEN or not config.METAAPI_ACCOUNT_ID:
        raise ValueError("METAAPI_TOKEN and METAAPI_ACCOUNT_ID must be configured")
    return MT5Feed(config.METAAPI_TOKEN, config.METAAPI_ACCOUNT_ID)
