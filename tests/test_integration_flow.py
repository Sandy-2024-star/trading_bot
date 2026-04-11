"""
Integration test for the full database and broker flow.
Verifies that components correctly interact with repositories in a realistic scenario.
"""

import pytest
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime

from database.base import Base
from execution.paper_broker import PaperBroker
from monitoring.pnl_tracker import PnLTracker
from execution.repositories import OrderRepository, TradeRepository
from monitoring.repositories.performance_repository import PerformanceRepository
from core.base_broker import OrderSide, OrderType, OrderStatus

@pytest.mark.asyncio
async def test_full_trading_flow_persistence():
    """
    Test that a complete trade cycle (place -> fill -> snapshot) 
    is correctly persisted across all repositories.
    """
    # 1. Setup in-memory database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = scoped_session(session_factory)
    
    # 2. Initialize Repositories
    order_repo = OrderRepository(session)
    trade_repo = TradeRepository(session)
    perf_repo = PerformanceRepository(session)
    
    # 3. Initialize Components with Repositories
    broker = PaperBroker(
        initial_balance=10000.0,
        order_repository=order_repo,
        trade_repository=trade_repo
    )
    # Manually add perf_repo to broker for discovery (standard pattern in main.py)
    broker.perf_repo = perf_repo
    
    tracker = PnLTracker(
        initial_balance=10000.0,
        performance_repository=perf_repo
    )
    
    await broker.connect()
    
    # 4. Simulate Price Update
    symbol = "BTCUSD"
    price = 50000.0
    await broker.update_price(symbol, price)
    
    # 5. Place a Market Order
    # This should trigger order_repo.save()
    order = await broker.place_order(
        symbol=symbol,
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=0.1
    )
    
    # 6. Verify Order Persistence
    db_order = order_repo.get_by_id(order.order_id)
    assert db_order is not None
    assert db_order.status == OrderStatus.FILLED
    assert db_order.filled_quantity == 0.1
    
    # 7. Verify Trade Persistence
    trades = trade_repo.get_by_order_id(order.order_id)
    assert len(trades) == 1
    assert trades[0].symbol == "BTCUSD"
    assert trades[0].quantity == 0.1
    
    # 8. Record a PnL Snapshot
    # This should trigger perf_repo.save_snapshot()
    portfolio_value = broker.get_portfolio_value()
    unrealized_pnl = sum(
        broker.calculate_position_pnl(symbol, broker.current_prices.get(symbol, 0))
        for symbol in broker.positions
    )

    tracker.record_snapshot(
        account_balance=broker.account_balance,
        position_value=portfolio_value - broker.account_balance,
        unrealized_pnl=unrealized_pnl,
        realized_pnl_since_start=broker.calculate_total_pnl()
    )

    
    # 9. Verify Performance Persistence
    latest_perf = perf_repo.get_latest()
    assert latest_perf is not None
    assert latest_perf.total_equity == broker.get_portfolio_value()
    
    # Cleanup
    await broker.disconnect()
    session.close()
    Base.metadata.drop_all(engine)
