"""
Test script for Yahoo Finance feed integration.
"""

import asyncio
import sys
import os

# Ensure trading_bot is in PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.yfinance_feed import YFinanceFeed

async def test_yfinance():
    print("Testing Yahoo Finance Feed...")
    feed = YFinanceFeed()
    
    symbols = ["BTCUSD", "EURUSD", "NIFTY50", "AAPL"]
    
    for symbol in symbols:
        print(f"\n--- Testing {symbol} ---")
        
        # 1. Test Ticker
        ticker = await feed.get_ticker(symbol)
        if ticker:
            print(f"Ticker: {ticker['symbol']} Price: {ticker['last_price']} via {ticker['provider']}")
        else:
            print(f"Ticker failed for {symbol}")
            
        # 2. Test Candlesticks
        df = await feed.get_candlesticks(symbol, timeframe="1h", limit=5)
        if not df.empty:
            print(f"Fetched {len(df)} candles. Latest close: {df['close'].iloc[-1]}")
        else:
            print(f"Candlesticks failed for {symbol}")

    print("\nYahoo Finance test complete!")

if __name__ == "__main__":
    asyncio.run(test_yfinance())
