"""
End-to-end test for trade persistence via PaperBroker and Repositories.
"""

import asyncio
import sys
import os
from datetime import datetime

# Ensure trading_bot is in PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Session, init_db
from execution.paper_broker import PaperBroker
from execution.repositories import OrderRepository, TradeRepository
from core.base_broker import OrderSide, OrderType
from monitoring.trade_history import TradeHistoryManager

async def test_end_to_end():
    """Simulate trades and verify persistence."""
    print("Starting End-to-End Persistence Test...")
    
    # Initialize DB
    init_db()
    
    # Setup database session and repositories
    session = Session()
    order_repo = OrderRepository(session)
    trade_repo = TradeRepository(session)
    
    # Initialize broker with repositories
    broker = PaperBroker(
        initial_balance=10000.0,
        order_repository=order_repo,
        trade_repository=trade_repo
    )
    
    await broker.connect()
    
    # 1. Update price
    symbol = "BTCUSD"
    price = 50000.0
    await broker.update_price(symbol, price)
    
    # 2. Place Market BUY
    print(f"\nPlacing MARKET BUY for {symbol} at ${price}...")
    buy_order = await broker.place_order(
        symbol=symbol,
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=0.1
    )
    print(f"BUY Order Status: {buy_order.status.value}")
    
    # 3. Update price again
    price = 55000.0
    await broker.update_price(symbol, price)
    
    # 4. Place Market SELL
    print(f"\nPlacing MARKET SELL for {symbol} at ${price}...")
    sell_order = await broker.place_order(
        symbol=symbol,
        side=OrderSide.SELL,
        order_type=OrderType.MARKET,
        quantity=0.1
    )
    print(f"SELL Order Status: {sell_order.status.value}")
    
    # 5. Verify persistence via TradeHistoryManager
    print("\nVerifying persistence via TradeHistoryManager...")
    history_manager = TradeHistoryManager(trade_repo, order_repo)
    history_manager.print_trade_summary(symbol)
    
    # Check data frames
    trades_df = history_manager.get_trade_history_df(symbol)
    orders_df = history_manager.get_order_history_df(symbol)
    
    print(f"\nTrades in DB: {len(trades_df)}")
    print(f"Orders in DB: {len(orders_df)}")
    
    if len(trades_df) >= 2 and len(orders_df) >= 2:
        print("\nSUCCESS: End-to-End Persistence Verified!")
    else:
        print("\nFAILURE: Persistent records not found as expected.")
    
    await broker.disconnect()
    session.close()

if __name__ == "__main__":
    asyncio.run(test_end_to_end())
