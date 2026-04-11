"""
Unit tests for database repositories using an in-memory SQLite database.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime

from database.base import Base
from execution.repositories.order_repository import OrderRepository
from execution.repositories.trade_repository import TradeRepository
from monitoring.repositories.performance_repository import PerformanceRepository
from core.base_broker import Order, Trade, OrderStatus, OrderSide, OrderType

# Setup in-memory database for testing
@pytest.fixture(scope="function")
def db_session():
    """Create a fresh in-memory database session for each test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = scoped_session(session_factory)
    yield session
    session.close()
    Base.metadata.drop_all(engine)

@pytest.fixture
def order_repo(db_session):
    return OrderRepository(db_session)

@pytest.fixture
def trade_repo(db_session):
    return TradeRepository(db_session)

@pytest.fixture
def perf_repo(db_session):
    return PerformanceRepository(db_session)

def test_order_repository_save_and_get(order_repo):
    """Test saving and retrieving an order."""
    order = Order(
        order_id="test_ord_1",
        symbol="BTCUSD",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=1.0,
        status=OrderStatus.PENDING
    )
    
    # Save
    order_repo.save(order)
    
    # Get by ID
    retrieved = order_repo.get_by_id("test_ord_1")
    assert retrieved is not None
    assert retrieved.symbol == "BTCUSD"
    assert retrieved.status == OrderStatus.PENDING

def test_order_repository_update(order_repo):
    """Test updating an existing order."""
    order = Order(
        order_id="test_ord_2",
        symbol="ETHUSD",
        side=OrderSide.SELL,
        order_type=OrderType.LIMIT,
        quantity=2.0,
        price=3000.0,
        status=OrderStatus.OPEN
    )
    order_repo.save(order)
    
    # Update status
    order.status = OrderStatus.FILLED
    order.filled_quantity = 2.0
    order.average_fill_price = 3005.0
    order_repo.save(order)
    
    retrieved = order_repo.get_by_id("test_ord_2")
    assert retrieved.status == OrderStatus.FILLED
    assert retrieved.filled_quantity == 2.0
    assert retrieved.average_fill_price == 3005.0

def test_trade_repository_save_and_get(trade_repo, order_repo, db_session):
    """Test saving a trade and retrieving it by order ID."""
    # Need an order first for the FK constraint (though SQLite doesn't always enforce by default)
    order = Order(
        order_id="ord_linked",
        symbol="BTCUSD",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=0.5,
        status=OrderStatus.FILLED
    )
    order_repo.save(order)
    
    trade = Trade(
        trade_id="trd_1",
        order_id="ord_linked",
        symbol="BTCUSD",
        side=OrderSide.BUY,
        quantity=0.5,
        price=50000.0,
        fees=50.0,
        timestamp=datetime.now(),
        pnl=0.0
    )
    
    trade_repo.save(trade)
    
    trades = trade_repo.get_by_order_id("ord_linked")
    assert len(trades) == 1
    assert trades[0].trade_id == "trd_1"
    assert trades[0].price == 50000.0

def test_performance_repository_snapshots(perf_repo):
    """Test saving and retrieving performance snapshots."""
    perf_repo.save_snapshot(total_equity=10000.0, total_pnl=0.0, daily_pnl=0.0)
    perf_repo.save_snapshot(total_equity=10500.0, total_pnl=500.0, daily_pnl=500.0)
    
    latest = perf_repo.get_latest()
    assert latest.total_equity == 10500.0
    assert latest.total_pnl == 500.0
    
    history = perf_repo.get_history()
    assert len(history) == 2
    assert history[0].total_equity == 10500.0 # Ordered by desc timestamp
