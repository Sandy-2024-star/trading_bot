"""
Dashboard data aggregator for comprehensive trading overview.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from loguru import logger

from config.config import config
from monitoring.pnl_tracker import PnLTracker
from monitoring.alerts import AlertManager
from core.base_broker import BaseBroker
from core.base_strategy import BaseStrategy
from risk.circuit_breaker import CircuitBreaker


class DashboardData:
    """
    Aggregates data from all system components for dashboard display.

    Provides unified view of:
    - Account status
    - Open positions
    - Recent trades
    - PnL metrics
    - Risk status
    - Recent alerts
    - System health
    """

    def __init__(
        self,
        pnl_tracker: PnLTracker,
        alert_manager: AlertManager,
        broker: BaseBroker,
        strategy: BaseStrategy,
        circuit_breaker: CircuitBreaker,
        trader: Optional[Any] = None
    ):
        self.pnl_tracker = pnl_tracker
        self.alert_manager = alert_manager
        self.broker = broker
        self.strategy = strategy
        self.circuit_breaker = circuit_breaker
        self.trader = trader
        self.start_time = datetime.now()

        logger.info("DashboardData initialized")

    def get_account_overview(self) -> Dict:
        """Get account status overview."""
        pnl_summary = self.pnl_tracker.get_summary()
        broker_stats = self.broker.get_statistics()

        return {
            "account_balance": broker_stats["account_balance"],
            "initial_balance": broker_stats["initial_balance"],
            "total_equity": pnl_summary["current_equity"],
            "total_return": pnl_summary["total_return"],
            "total_return_pct": pnl_summary["total_return_pct"],
            "realized_pnl": pnl_summary["realized_pnl"],
            "unrealized_pnl": pnl_summary["unrealized_pnl"],
            "daily_pnl": pnl_summary["daily_pnl"],
            "daily_pnl_pct": pnl_summary["daily_pnl_pct"]
        }

    def get_positions(self) -> List[Dict]:
        """Get all open positions with current PnL."""
        positions = []
        open_positions = self.strategy.get_open_positions()

        for position in open_positions:
            # Get current price from broker
            current_price = self.broker.current_prices.get(position.symbol, 0.0)

            # Calculate unrealized PnL
            unrealized_pnl = position.calculate_pnl(current_price) if current_price > 0 else 0.0
            unrealized_pnl_pct = position.calculate_pnl_percent(current_price) if current_price > 0 else 0.0

            positions.append({
                "symbol": position.symbol,
                "side": position.side.value,
                "size": position.size,
                "entry_price": position.entry_price,
                "current_price": current_price,
                "stop_loss": position.stop_loss,
                "take_profit": position.take_profit,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pnl_pct": unrealized_pnl_pct,
                "entry_time": position.timestamp,
                "duration": str(datetime.now() - position.timestamp).split('.')[0]
            })

        return positions

    def get_recent_trades(self, count: int = 10) -> List[Dict]:
        """Get recent closed trades."""
        all_trades = self.broker.get_all_trades()
        recent_trades = all_trades[-count:] if len(all_trades) > count else all_trades

        trades = []
        for trade in reversed(recent_trades):  # Most recent first
            trades.append({
                "trade_id": trade.trade_id,
                "symbol": trade.symbol,
                "side": trade.side.value,
                "quantity": trade.quantity,
                "price": trade.price,
                "fees": trade.fees,
                "pnl": trade.pnl,
                "timestamp": trade.timestamp
            })

        return trades

    def get_performance_metrics(self) -> Dict:
        """Get performance statistics."""
        strategy_stats = self.strategy.get_stats()
        broker_stats = self.broker.get_statistics()

        return {
            "total_trades": broker_stats["total_trades"],
            "winning_trades": strategy_stats["winning_trades"],
            "losing_trades": strategy_stats["losing_trades"],
            "win_rate": strategy_stats["win_rate"],
            "total_pnl": strategy_stats["total_pnl"],
            "total_fees": broker_stats["total_fees"],
            "attribution": getattr(self.pnl_tracker, 'performance_attribution', {})
        }

    def get_risk_status(self) -> Dict:
        """Get risk management status."""
        cb_status = self.circuit_breaker.get_status()

        return {
            "circuit_breaker_state": cb_status["state"],
            "trip_reason": cb_status.get("trip_reason"),
            "consecutive_losses": cb_status["consecutive_losses"],
            "daily_trades": cb_status["daily_trades"],
            "daily_pnl": cb_status["daily_pnl"],
            "cooldown_remaining": cb_status.get("cooldown_remaining", 0),
            "trading_allowed": cb_status["state"] == "closed"
        }

    def get_recent_alerts(self, count: int = 10) -> List[Dict]:
        """Get recent alerts."""
        alerts = self.alert_manager.get_recent_alerts(count)

        return [{
            "type": alert.alert_type.value,
            "level": alert.level.value,
            "message": alert.message,
            "timestamp": alert.timestamp,
            "data": alert.data
        } for alert in alerts]

    def get_system_status(self) -> Dict:
        """Get system health status."""
        uptime = datetime.now() - self.start_time
        uptime_str = str(uptime).split('.')[0]  # Remove microseconds

        open_positions = len(self.strategy.get_open_positions())
        open_orders = len(self.broker.get_all_orders())

        return {
            "status": "running",
            "is_paused": getattr(self.trader, 'paused', False),
            "is_running": getattr(self.trader, 'running', False),
            "uptime": uptime_str,
            "start_time": self.start_time,
            "open_positions": open_positions,
            "open_orders": open_orders,
            "strategy_name": self.strategy.name
        }

    def get_market_context(self) -> Dict:
        """Get latest market context per symbol for dashboard display."""
        context_map = self.strategy.get_market_context()
        return context_map if isinstance(context_map, dict) else {}

    def get_latest_signals(self) -> List[Dict]:
        """Get the most recent signal generated for each symbol."""
        latest_signals = self.strategy.get_latest_signal()
        if not isinstance(latest_signals, dict):
            return []

        signal_rows = []
        for symbol, signal in latest_signals.items():
            if signal is None:
                continue
            signal_rows.append({
                "symbol": symbol,
                "side": signal.side.value,
                "strength": signal.strength,
                "timestamp": signal.timestamp,
                "sentiment_label": signal.indicators.get("sentiment_label", "NEUTRAL"),
                "sentiment_score": signal.indicators.get("sentiment_score", 0.0),
                "article_count": signal.indicators.get("article_count", 0),
                "rsi": signal.indicators.get("rsi"),
                "macd": signal.indicators.get("macd"),
                "close": signal.indicators.get("close"),
            })
        signal_rows.sort(key=lambda row: row["timestamp"], reverse=True)
        return signal_rows

    def get_broker_status(self) -> Dict:
        """Get current execution mode and real-broker readiness details."""
        provider = config.REAL_BROKER_PROVIDER
        broker_name = getattr(self.broker, "name", self.broker.__class__.__name__)
        connected = bool(getattr(self.broker, "connected", False))

        required_fields = {
            "oanda": {
                "api_key": bool(config.OANDA_API_KEY),
                "account_id": bool(config.OANDA_ACCOUNT_ID),
            },
            "fxcm": {
                "api_key": bool(config.FXCM_API_KEY),
                "account_id": bool(config.FXCM_ACCOUNT_ID),
            },
            "zerodha": {
                "api_key": bool(config.ZERODHA_API_KEY),
                "api_secret": bool(config.ZERODHA_API_SECRET),
                "access_token": bool(config.ZERODHA_ACCESS_TOKEN),
            },
            "crypto_com": {
                "api_key": bool(config.CRYPTO_COM_API_KEY),
                "secret_key": bool(config.CRYPTO_COM_SECRET_KEY),
            },
        }.get(provider, {})

        ready = bool(required_fields) and all(required_fields.values())

        return {
            "active_broker": broker_name,
            "active_mode": "paper" if "paper" in broker_name.lower() else "real",
            "connected": connected,
            "execution_mode": config.EXECUTION_MODE,
            "real_broker_provider": provider,
            "real_broker_implemented": False,
            "real_broker_ready": ready,
            "required_credentials": required_fields,
            "status_message": (
                f"{provider} credentials configured, but live broker integration is not implemented yet."
                if ready else
                f"{provider} live broker is not ready. Missing credentials or implementation."
            ),
        }

    def get_full_dashboard(self) -> Dict:
        """Get complete dashboard data."""
        return {
            "timestamp": datetime.now(),
            "account": self.get_account_overview(),
            "positions": self.get_positions(),
            "recent_trades": self.get_recent_trades(),
            "performance": self.get_performance_metrics(),
            "risk": self.get_risk_status(),
            "alerts": self.get_recent_alerts(),
            "system": self.get_system_status(),
            "broker_status": self.get_broker_status(),
            "market_context": self.get_market_context(),
            "latest_signals": self.get_latest_signals(),
        }

    def print_dashboard(self):
        """Print dashboard to console."""
        dashboard = self.get_full_dashboard()

        print("\n" + "="*80)
        print("TRADING DASHBOARD")
        print("="*80)
        print(f"Time: {dashboard['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Uptime: {dashboard['system']['uptime']}")
        print("="*80)

        # Account overview
        account = dashboard['account']
        print("\n💰 ACCOUNT OVERVIEW")
        print(f"  Balance:          ${account['account_balance']:>12,.2f}")
        print(f"  Total Equity:     ${account['total_equity']:>12,.2f}")
        print(f"  Total Return:     ${account['total_return']:>12,.2f}  ({account['total_return_pct']:>6.2f}%)")
        print(f"  Today's PnL:      ${account['daily_pnl']:>12,.2f}  ({account['daily_pnl_pct']:>6.2f}%)")
        print(f"  Realized PnL:     ${account['realized_pnl']:>12,.2f}")
        print(f"  Unrealized PnL:   ${account['unrealized_pnl']:>12,.2f}")

        # Open positions
        positions = dashboard['positions']
        print(f"\n📊 OPEN POSITIONS ({len(positions)})")
        if positions:
            for pos in positions:
                pnl_sign = "+" if pos['unrealized_pnl'] >= 0 else ""
                print(f"  {pos['symbol']:8s} {pos['side']:4s} {pos['size']:>8.4f} @ "
                      f"${pos['entry_price']:>8,.2f} → ${pos['current_price']:>8,.2f} "
                      f"[{pnl_sign}${pos['unrealized_pnl']:>8,.2f} ({pnl_sign}{pos['unrealized_pnl_pct']:>6.2f}%)]")
        else:
            print("  No open positions")

        # Performance
        perf = dashboard['performance']
        print(f"\n📈 PERFORMANCE")
        print(f"  Total Trades:     {perf['total_trades']:>12,}")
        print(f"  Winning Trades:   {perf['winning_trades']:>12,}")
        print(f"  Losing Trades:    {perf['losing_trades']:>12,}")
        print(f"  Win Rate:                           {perf['win_rate']:>6.2f}%")
        print(f"  Total Fees:       ${perf['total_fees']:>12,.2f}")

        # Risk status
        risk = dashboard['risk']
        print(f"\n⚠️  RISK STATUS")
        print(f"  Circuit Breaker:  {risk['circuit_breaker_state']:>12s}")
        print(f"  Trading Allowed:  {'YES' if risk['trading_allowed'] else 'NO':>12s}")
        print(f"  Consecutive Loss: {risk['consecutive_losses']:>12,}")
        print(f"  Daily Trades:     {risk['daily_trades']:>12,}")

        market_context = dashboard['market_context']
        if market_context:
            print(f"\n🌐 MARKET CONTEXT")
            for symbol, context in market_context.items():
                rate = context.get('eurusd_rate')
                rate_text = f"{rate:.5f}" if isinstance(rate, (int, float)) else "n/a"
                print(
                    f"  {symbol:8s} sentiment={context.get('sentiment_label', 'NEUTRAL'):>8s} "
                    f"({context.get('sentiment_score', 0.0):>5.2f}) "
                    f"articles={context.get('article_count', 0):>3d} EUR/USD={rate_text}"
                )

        # Recent trades
        trades = dashboard['recent_trades']
        print(f"\n📝 RECENT TRADES (showing last 5)")
        for trade in trades[:5]:
            pnl_sign = "+" if trade['pnl'] >= 0 else ""
            print(f"  {trade['timestamp'].strftime('%H:%M:%S')} {trade['symbol']:8s} "
                  f"{trade['side']:4s} {trade['quantity']:>8.4f} @ ${trade['price']:>8,.2f} "
                  f"PnL: {pnl_sign}${trade['pnl']:>8,.2f}")

        # Recent alerts
        alerts = dashboard['alerts']
        if alerts:
            print(f"\n🔔 RECENT ALERTS (showing last 5)")
            for alert in alerts[:5]:
                print(f"  [{alert['timestamp'].strftime('%H:%M:%S')}] [{alert['level']:8s}] {alert['message'][:60]}")

        print("\n" + "="*80 + "\n")


# Example usage
def main():
    from execution.paper_broker import PaperBroker
    from strategy.signal_strategy import TechnicalSignalStrategy
    from risk.circuit_breaker import CircuitBreaker
    import asyncio

    async def run_example():
        # Initialize components
        pnl_tracker = PnLTracker(initial_balance=10000.0)
        alert_manager = AlertManager()
        broker = PaperBroker(initial_balance=10000.0)
        await broker.connect()
        strategy = TechnicalSignalStrategy()
        circuit_breaker = CircuitBreaker()

        # Create dashboard
        dashboard = DashboardData(
            pnl_tracker=pnl_tracker,
            alert_manager=alert_manager,
            broker=broker,
            strategy=strategy,
            circuit_breaker=circuit_breaker
        )

        # Record some activity
        pnl_tracker.record_snapshot(10000.0, 0.0, 0.0, 0.0)
        alert_manager.position_opened("BTCUSD", "buy", 0.1, 50000.0, 47500.0, 52500.0)

        # Print dashboard
        dashboard.print_dashboard()

        # Get full data
        full_data = dashboard.get_full_dashboard()
        print("Full dashboard data keys:", full_data.keys())

        await broker.disconnect()

    asyncio.run(run_example())


if __name__ == "__main__":
    main()
