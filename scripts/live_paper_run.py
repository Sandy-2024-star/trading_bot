"""
Live Run Script (Paper Trading Mode).
Launches the full system with all v3.0 features enabled.
"""

import asyncio
import sys
import os
from loguru import logger

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.factory import create_market_data_feed
from execution.paper_broker import PaperBroker
from execution.repositories import OrderRepository, TradeRepository, PositionRepository
from monitoring.repositories.performance_repository import PerformanceRepository
from monitoring.live_trader import LiveTrader
from strategy.factory import create_strategy
from risk.position_sizer import PositionSizer, SizingMethod
from risk.stop_loss import StopLossManager, StopLossType
from risk.circuit_breaker import CircuitBreaker
from database import init_db, Session

async def run_enterprise_bot():
    logger.info("🏢 Starting Enterprise Trading Bot (v3.0)...")
    
    # 1. Initialize Database
    init_db()
    session = Session()
    
    # 2. Setup Repositories
    order_repo = OrderRepository(session)
    trade_repo = TradeRepository(session)
    pos_repo = PositionRepository(session)
    perf_repo = PerformanceRepository(session)
    
    # 3. Setup Components
    feed = create_market_data_feed()
    
    # Initialize Paper Broker with full persistence
    broker = PaperBroker(
        initial_balance=10000.0,
        order_repository=order_repo,
        trade_repository=trade_repo
    )
    # Inject remaining repos
    broker.pos_repo = pos_repo
    broker.perf_repo = perf_repo
    
    # Strategy Factory (loads tuned params + AI models)
    strategy = create_strategy(name="EnterpriseSignalStrategy", strategy_type="technical")
    
    # Risk Management
    position_sizer = PositionSizer(
        method=SizingMethod.RISK_BASED, 
        risk_per_trade=0.02,
        max_portfolio_heat=0.06
    )
    
    stop_loss_manager = StopLossManager(
        stop_loss_type=StopLossType.TRAILING,
        stop_loss_percent=0.02 # Tight 2% trailing stop
    )
    
    circuit_breaker = CircuitBreaker(
        max_daily_loss_percent=0.05,
        max_consecutive_losses=3
    )
    
    # 4. Initialize Live Trader
    trader = LiveTrader(
        feed=feed,
        broker=broker,
        strategy=strategy,
        position_sizer=position_sizer,
        stop_loss_manager=stop_loss_manager,
        circuit_breaker=circuit_breaker,
        symbols=["BTCUSD", "ETHUSD", "EURUSD", "RELIANCE"],
        update_interval=60,
        enable_telegram=False
    )
    
    # Link trader to broker for PnL and metrics
    broker.pnl_tracker = trader.pnl_tracker
    
    try:
        await trader.start()
    except KeyboardInterrupt:
        await trader.stop()
    finally:
        await feed.close()
        await broker.disconnect()
        session.close()

if __name__ == "__main__":
    asyncio.run(run_enterprise_bot())
