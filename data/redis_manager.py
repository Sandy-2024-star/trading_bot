"""
Redis connection management for the trading bot.
Provides a central manager for caching market data.
"""

import redis
from loguru import logger
from config.config import config

class RedisManager:
    """Manages Redis connections and basic operations."""

    _instance = None

    def __new__(cls):
        """Singleton pattern to ensure only one Redis connection pool exists."""
        if cls._instance is None:
            cls._instance = super(RedisManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the Redis client."""
        if self._initialized:
            return

        self.client = None
        self.connected = False
        self._initialized = True
        self._connect()

    def _connect(self):
        """Establish connection to Redis."""
        try:
            self.client = redis.Redis(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                db=config.REDIS_DB,
                password=config.REDIS_PASSWORD if config.REDIS_PASSWORD else None,
                decode_responses=True,
                socket_timeout=2
            )
            # Test connection
            self.client.ping()
            self.connected = True
            logger.info(f"Connected to Redis at {config.REDIS_HOST}:{config.REDIS_PORT}")
        except (redis.ConnectionError, redis.TimeoutError) as e:
            self.connected = False
            logger.warning(f"Could not connect to Redis: {e}. Caching will be disabled.")

    def get_client(self) -> redis.Redis:
        """Get the Redis client instance."""
        if not self.connected:
            self._connect()
        return self.client

    def is_available(self) -> bool:
        """Check if Redis is available."""
        if not self.connected:
            self._connect()
        return self.connected

# Global instance
redis_manager = RedisManager()
