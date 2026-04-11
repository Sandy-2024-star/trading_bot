"""
Configuration loader for trading system.
Loads settings from environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger


def _get_bool(name: str, default: bool = False) -> bool:
    """Parse a boolean environment variable."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


# Load .env file from config directory
config_dir = Path(__file__).parent
env_path = config_dir / ".env"

if env_path.exists():
    load_dotenv(env_path)
    logger.info(f"Loaded configuration from {env_path}")
else:
    logger.warning(
        f"No .env file found at {env_path}. Using environment variables or defaults."
    )


class Config:
    """
    Central configuration class.
    """

    # CoinGecko
    COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "")

    # Crypto.com
    CRYPTO_COM_API_KEY = os.getenv("CRYPTO_COM_API_KEY", "")
    CRYPTO_COM_SECRET_KEY = os.getenv("CRYPTO_COM_SECRET_KEY", "")

    # OANDA
    OANDA_API_KEY = os.getenv("OANDA_API_KEY", "")
    OANDA_ACCOUNT_ID = os.getenv("OANDA_ACCOUNT_ID", "")
    OANDA_ENVIRONMENT = os.getenv("OANDA_ENVIRONMENT", "practice")

    # FXCM
    FXCM_API_KEY = os.getenv("FXCM_API_KEY", "")
    FXCM_ACCOUNT_ID = os.getenv("FXCM_ACCOUNT_ID", "")

    # Zerodha
    ZERODHA_API_KEY = os.getenv("ZERODHA_API_KEY", "")
    ZERODHA_API_SECRET = os.getenv("ZERODHA_API_SECRET", "")
    ZERODHA_ACCESS_TOKEN = os.getenv("ZERODHA_ACCESS_TOKEN", "")

    # Shoonya (Finvasia)
    SHOONYA_USER_ID = os.getenv("SHOONYA_USER_ID", "")
    SHOONYA_PASSWORD = os.getenv("SHOONYA_PASSWORD", "")
    SHOONYA_API_KEY = os.getenv("SHOONYA_API_KEY", "")
    SHOONYA_VENDOR_CODE = os.getenv("SHOONYA_VENDOR_CODE", "")
    SHOONYA_IMEI = os.getenv("SHOONYA_IMEI", "abc12345")
    SHOONYA_TOTP_SECRET = os.getenv("SHOONYA_TOTP_SECRET", "")

    # MetaApi (MT5)
    METAAPI_TOKEN = os.getenv("METAAPI_TOKEN", "")
    METAAPI_ACCOUNT_ID = os.getenv("METAAPI_ACCOUNT_ID", "")
    METAAPI_BROKER_SERVER = os.getenv("METAAPI_BROKER_SERVER", "MetaQuotes-Demo")

    # News APIs
    NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
    ALPHA_VANTAGE_API_KEY = os.getenv(
        "ALPHA_VANTAGE_API_KEY", os.getenv("ALPHA_VANTAGE_KEY", "")
    )
    ALPHA_VANTAGE_KEY = ALPHA_VANTAGE_API_KEY

    # Local LLM / LiteLLM
    SENTIMENT_ANALYZER = os.getenv("SENTIMENT_ANALYZER", "rule_based").lower()
    LOCAL_LLM_ENABLED = _get_bool("LOCAL_LLM_ENABLED", False)
    LOCAL_LLM_BASE_URL = os.getenv(
        "LOCAL_LLM_BASE_URL", "http://localhost:8000"
    ).rstrip("/")
    LOCAL_LLM_ENDPOINT = os.getenv("LOCAL_LLM_ENDPOINT", "/v1/chat/completions")
    LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "qwen-coder-3b")
    LOCAL_LLM_API_KEY = os.getenv("LOCAL_LLM_API_KEY", "")
    LOCAL_LLM_TIMEOUT_SECONDS = float(os.getenv("LOCAL_LLM_TIMEOUT_SECONDS", "20"))
    LOCAL_LLM_TEMPERATURE = float(os.getenv("LOCAL_LLM_TEMPERATURE", "0.1"))

    # Data providers
    MARKET_DATA_PROVIDER = os.getenv("MARKET_DATA_PROVIDER", "coingecko").lower()
    FOREX_DATA_PROVIDER = os.getenv("FOREX_DATA_PROVIDER", "alpha_vantage").lower()
    NEWS_DATA_PROVIDER = os.getenv("NEWS_DATA_PROVIDER", "newsapi").lower()

    # Execution
    EXECUTION_MODE = os.getenv("EXECUTION_MODE", "paper").lower()
    REAL_BROKER_PROVIDER = os.getenv("REAL_BROKER_PROVIDER", "mt5").lower()

    # Database
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB = os.getenv("POSTGRES_DB", "trading_bot")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")

    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

    # Trading Parameters
    MAX_POSITION_SIZE = float(os.getenv("MAX_POSITION_SIZE", "10000"))
    RISK_PER_TRADE = float(os.getenv("RISK_PER_TRADE", "0.02"))
    STOP_LOSS_PERCENT = float(os.getenv("STOP_LOSS_PERCENT", "0.05"))

    # System
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

    # Dashboard Authentication
    DASHBOARD_USERNAME = os.getenv("DASHBOARD_USERNAME", "admin")
    DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "admin123")  # In production, use a strong password
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "7d983248792384792384723984723984") # Change this in production!
    JWT_ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24 hours

    @classmethod
    def get_postgres_url(cls) -> str:
        """Get PostgreSQL connection URL."""
        return f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"

    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment."""
        return cls.ENVIRONMENT == "production"

    @classmethod
    def validate(cls) -> bool:
        """
        Validate critical configuration values.

        Returns:
            True if configuration is valid, False otherwise
        """
        errors = []

        # Check crypto API keys if needed
        if not cls.CRYPTO_COM_API_KEY:
            logger.warning("CRYPTO_COM_API_KEY not set")

        # Add more validation as needed
        if cls.RISK_PER_TRADE > 0.1:
            errors.append("RISK_PER_TRADE should not exceed 10%")

        if cls.STOP_LOSS_PERCENT > 0.2:
            errors.append("STOP_LOSS_PERCENT should not exceed 20%")

        valid_analyzers = {"rule_based", "local_llm", "auto"}
        if cls.SENTIMENT_ANALYZER not in valid_analyzers:
            errors.append(
                f"SENTIMENT_ANALYZER must be one of {sorted(valid_analyzers)}"
            )

        if cls.LOCAL_LLM_TIMEOUT_SECONDS <= 0:
            errors.append("LOCAL_LLM_TIMEOUT_SECONDS must be greater than 0")

        if errors:
            for error in errors:
                logger.error(f"Configuration error: {error}")
            return False

        logger.info("Configuration validation passed")
        return True


# Singleton instance
config = Config()
