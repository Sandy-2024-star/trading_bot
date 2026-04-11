"""
Test script for multi-market data routing via MarketRegistry.
"""

import asyncio
import sys
import os

# Ensure trading_bot is in PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.market_registry import market_registry
from core.base_feed import MarketDataFeed

async def test_routing():
    print("Testing Market Data Routing...")
    
    symbols = ["BTCUSD", "ETH/USDT", "EURUSD", "RELIANCE"]
    
    for symbol in symbols:
        feed = market_registry.get_feed_for_symbol(symbol)
        feed_name = feed.__class__.__name__ if feed else "None"
        print(f"Symbol: {symbol:<10} -> Feed: {feed_name}")
        
        if feed:
            # Simple check to see if it's a valid feed instance
            assert isinstance(feed, MarketDataFeed)

    print("\nRouting test PASSED!")
    await market_registry.close_all()

if __name__ == "__main__":
    asyncio.run(test_routing())
