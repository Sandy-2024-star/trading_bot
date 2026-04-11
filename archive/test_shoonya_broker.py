"""
Test script for Shoonya (Finvasia) Broker integration.
"""

import asyncio
import sys
import os

# Ensure trading_bot is in PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from execution.brokers.shoonya_broker import ShoonyaBroker

async def test_shoonya_broker():
    print("Testing Shoonya (Finvasia) Broker...")
    broker = ShoonyaBroker()
    
    # Connect and login
    print("\n[1] Attempting to connect/login...")
    connected = await broker.connect()
    
    if not connected:
        print("Failed to connect ShoonyaBroker. Check your .env credentials.")
        return

    print("Successfully connected ShoonyaBroker!")

    # Check Balance
    print(f"Account Balance: ${broker.account_balance}")

    # Check Positions
    print("\n[2] Fetching open positions...")
    positions = await broker.get_positions()
    if positions:
        print(f"Found {len(positions)} positions.")
        for pos in positions:
            print(f"- {pos.get('tsym')}: Qty={pos.get('netqty')}, PnL={pos.get('rpnl')}")
    else:
        print("No open positions found.")

    await broker.disconnect()
    print("\nShoonya broker test complete!")

if __name__ == "__main__":
    asyncio.run(test_shoonya_broker())
