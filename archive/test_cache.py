"""
Test script for Redis caching layer.
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime

# Ensure trading_bot is in PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.redis_manager import redis_manager
from data.market_cache import market_cache

def test_cache():
    """Test Redis connection and market data caching."""
    print("Testing Market Data Cache...")
    
    # 1. Check Redis availability
    if not redis_manager.is_available():
        print("Redis is NOT available. Skipping cache tests.")
        print("To run these tests, ensure a Redis server is running at localhost:6379")
        return

    print("Redis is available.")
    
    # 2. Test Ticker Cache
    symbol = "BTCUSD"
    ticker_data = {
        "symbol": symbol,
        "last_price": 50000.0,
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"Caching ticker for {symbol}...")
    market_cache.set_ticker(symbol, ticker_data, expire=10)
    
    retrieved_ticker = market_cache.get_ticker(symbol)
    if retrieved_ticker and retrieved_ticker["last_price"] == 50000.0:
        print("Ticker cache test PASSED!")
    else:
        print("Ticker cache test FAILED!")

    # 3. Test Candlestick Cache
    print(f"Caching candlesticks for {symbol}...")
    df = pd.DataFrame({
        "timestamp": [datetime.now()],
        "open": [50000.0],
        "high": [51000.0],
        "low": [49000.0],
        "close": [50500.0],
        "volume": [100.0]
    })
    
    timeframe = "1h"
    market_cache.set_candlesticks(symbol, timeframe, df, expire=10)
    
    retrieved_df = market_cache.get_candlesticks(symbol, timeframe)
    if retrieved_df is not None and not retrieved_df.empty:
        if retrieved_df["close"].iloc[0] == 50500.0:
            print("Candlestick cache test PASSED!")
        else:
            print(f"Candlestick cache test FAILED! Data mismatch: {retrieved_df['close'].iloc[0]}")
    else:
        print("Candlestick cache test FAILED! No data retrieved.")

if __name__ == "__main__":
    test_cache()
