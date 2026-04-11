"""
Test script for Shoonya (Finvasia) integration.
"""

import asyncio
import sys
import os

# Ensure trading_bot is in PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from data.indian.shoonya_feed import ShoonyaFeed

async def test_shoonya():
    print("Testing Shoonya (Finvasia) Feed...")
    feed = ShoonyaFeed()
    
    # Connect and login
    print("\n[1] Attempting to connect/login...")
    connected = await feed.connect()
    
    if not connected:
        print("Failed to connect to Shoonya. Check your .env credentials and TOTP secret.")
        return

    print("Successfully connected to Shoonya!")

    # Test symbols
    symbols = ["NIFTYBEES", "RELIANCE", "MCX|GOLD"]
    
    for symbol in symbols:
        print(f"\n--- Testing {symbol} ---")
        
        # 1. Test Ticker
        print(f"Fetching ticker for {symbol}...")
        ticker = await feed.get_ticker(symbol)
        if ticker:
            print(f"Ticker: {ticker['symbol']} Price: {ticker['last_price']} via {ticker['provider']}")
        else:
            print(f"Ticker failed for {symbol}")
            
        # 2. Test Candlesticks
        print(f"Fetching 1-minute candles for {symbol}...")
        df = await feed.get_candlesticks(symbol, timeframe="1m", limit=5)
        if not df.empty:
            print(f"Fetched {len(df)} candles. Latest close: {df['close'].iloc[-1]}")
            print(df.tail())
        else:
            print(f"Candlesticks failed for {symbol}")

    print("\nShoonya integration test complete!")

if __name__ == "__main__":
    asyncio.run(test_shoonya())
