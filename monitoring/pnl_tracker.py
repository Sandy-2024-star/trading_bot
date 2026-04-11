"""
PnL (Profit and Loss) tracker for real-time performance monitoring.
"""

import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from loguru import logger
from monitoring.repositories.performance_repository import PerformanceRepository


@dataclass
class PnLSnapshot:
    """Snapshot of PnL at a point in time."""
    timestamp: datetime
    realized_pnl: float
    unrealized_pnl: float
    total_pnl: float
    account_balance: float
    position_value: float
    total_equity: float
    daily_pnl: float
    daily_pnl_pct: float


class PnLTracker:
    """
    Tracks profit and loss metrics in real-time.

    Features:
    - Real-time PnL calculation
    - Daily/weekly/monthly PnL aggregation
    - Historical PnL tracking
    - Performance metrics over time
    """

    def __init__(
        self, 
        initial_balance: float, 
        performance_repository: Optional[PerformanceRepository] = None,
        web_dashboard: Optional[Any] = None
    ):
        self.initial_balance = initial_balance
        self.snapshots: List[PnLSnapshot] = []
        self.daily_start_balance = initial_balance
        self.daily_start_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.perf_repo = performance_repository
        self.web_dashboard = web_dashboard
        
        # Attribution: Track PnL by signal type
        self.performance_attribution = {
            "technical": 0.0,
            "sentiment": 0.0,
            "ai": 0.0,
            "mtf": 0.0,
            "manual": 0.0
        }

        logger.info(f"PnLTracker initialized with ${initial_balance:,.2f}")

    def update_attribution(self, signal_type: str, pnl: float):
        """
        Attribute realized PnL to a specific signal or strategy component.
        """
        if signal_type in self.performance_attribution:
            self.performance_attribution[signal_type] += pnl
            logger.debug(f"Attributed ${pnl:.2f} to {signal_type}. Total: ${self.performance_attribution[signal_type]:.2f}")

    def record_snapshot(
        self,
        account_balance: float,
        position_value: float,
        unrealized_pnl: float,
        realized_pnl_since_start: float
    ):
        """
        Record a PnL snapshot.

        Args:
            account_balance: Current cash balance
            position_value: Value of open positions
            unrealized_pnl: Unrealized PnL from open positions
            realized_pnl_since_start: Total realized PnL since inception
        """
        total_equity = account_balance + position_value
        total_pnl = realized_pnl_since_start + unrealized_pnl

        # Calculate daily PnL
        daily_pnl = total_equity - self.daily_start_balance
        daily_pnl_pct = (daily_pnl / self.daily_start_balance) * 100 if self.daily_start_balance > 0 else 0.0

        snapshot = PnLSnapshot(
            timestamp=datetime.now(),
            realized_pnl=realized_pnl_since_start,
            unrealized_pnl=unrealized_pnl,
            total_pnl=total_pnl,
            account_balance=account_balance,
            position_value=position_value,
            total_equity=total_equity,
            daily_pnl=daily_pnl,
            daily_pnl_pct=daily_pnl_pct
        )

        self.snapshots.append(snapshot)

        # Persist to database if repository is available
        if self.perf_repo:
            try:
                self.perf_repo.save_snapshot(
                    total_equity=total_equity,
                    total_pnl=total_pnl,
                    daily_pnl=daily_pnl
                )
            except Exception as e:
                logger.warning(f"Failed to persist performance snapshot: {e}")

        # Check if we need to reset daily tracking
        now = datetime.now()
        if now.date() > self.daily_start_time.date():
            self._reset_daily_tracking(total_equity)

        # Broadcast update if dashboard is available
        if self.web_dashboard:
            try:
                dashboard_update = self.web_dashboard.dashboard_data.get_full_dashboard()
                # Use create_task to avoid blocking the main loop
                asyncio.create_task(self.web_dashboard.broadcast(dashboard_update))
            except Exception as e:
                logger.warning(f"Failed to broadcast dashboard update: {e}")

        logger.debug(f"PnL snapshot recorded: equity=${total_equity:,.2f}, daily PnL=${daily_pnl:,.2f}")

    def get_latest_snapshot(self) -> Optional[PnLSnapshot]:
        """Get the most recent PnL snapshot."""
        return self.snapshots[-1] if self.snapshots else None

    def get_current_return(self) -> float:
        """Get current total return percentage."""
        latest = self.get_latest_snapshot()
        if not latest:
            return 0.0
        return ((latest.total_equity - self.initial_balance) / self.initial_balance) * 100

    def get_daily_pnl(self) -> Dict:
        """Get today's PnL statistics."""
        latest = self.get_latest_snapshot()
        if not latest:
            return {
                "daily_pnl": 0.0,
                "daily_pnl_pct": 0.0,
                "daily_high": 0.0,
                "daily_low": 0.0
            }

        # Get today's snapshots
        today_snapshots = [
            s for s in self.snapshots
            if s.timestamp.date() == datetime.now().date()
        ]

        if not today_snapshots:
            return {
                "daily_pnl": 0.0,
                "daily_pnl_pct": 0.0,
                "daily_high": 0.0,
                "daily_low": 0.0
            }

        daily_pnls = [s.daily_pnl for s in today_snapshots]

        return {
            "daily_pnl": latest.daily_pnl,
            "daily_pnl_pct": latest.daily_pnl_pct,
            "daily_high": max(daily_pnls),
            "daily_low": min(daily_pnls)
        }

    def get_period_pnl(self, days: int) -> Dict:
        """
        Get PnL for a specific period.

        Args:
            days: Number of days to look back

        Returns:
            Dict with period PnL statistics
        """
        cutoff_time = datetime.now() - timedelta(days=days)
        period_snapshots = [s for s in self.snapshots if s.timestamp >= cutoff_time]

        if not period_snapshots:
            return {
                "period_pnl": 0.0,
                "period_pnl_pct": 0.0,
                "period_high": 0.0,
                "period_low": 0.0
            }

        start_equity = period_snapshots[0].total_equity
        end_equity = period_snapshots[-1].total_equity
        period_pnl = end_equity - start_equity
        period_pnl_pct = (period_pnl / start_equity) * 100 if start_equity > 0 else 0.0

        equities = [s.total_equity for s in period_snapshots]

        return {
            "period_pnl": period_pnl,
            "period_pnl_pct": period_pnl_pct,
            "period_high": max(equities),
            "period_low": min(equities),
            "period_days": days
        }

    def get_equity_curve(self) -> pd.DataFrame:
        """Get equity curve as DataFrame."""
        if not self.snapshots:
            return pd.DataFrame()

        data = [{
            'timestamp': s.timestamp,
            'equity': s.total_equity,
            'cash': s.account_balance,
            'positions': s.position_value,
            'realized_pnl': s.realized_pnl,
            'unrealized_pnl': s.unrealized_pnl,
            'total_pnl': s.total_pnl,
            'daily_pnl': s.daily_pnl
        } for s in self.snapshots]

        return pd.DataFrame(data)

    def get_summary(self) -> Dict:
        """Get comprehensive PnL summary."""
        latest = self.get_latest_snapshot()
        if not latest:
            return {
                "initial_balance": self.initial_balance,
                "current_equity": self.initial_balance,
                "total_return": 0.0,
                "total_return_pct": 0.0,
                "realized_pnl": 0.0,
                "unrealized_pnl": 0.0,
                "daily_pnl": 0.0,
                "daily_pnl_pct": 0.0
            }

        return {
            "initial_balance": self.initial_balance,
            "current_equity": latest.total_equity,
            "total_return": latest.total_pnl,
            "total_return_pct": self.get_current_return(),
            "realized_pnl": latest.realized_pnl,
            "unrealized_pnl": latest.unrealized_pnl,
            "daily_pnl": latest.daily_pnl,
            "daily_pnl_pct": latest.daily_pnl_pct,
            **self.get_period_pnl(7),  # Weekly stats
        }

    def print_summary(self):
        """Print PnL summary to console."""
        summary = self.get_summary()
        daily = self.get_daily_pnl()

        print("\n" + "="*60)
        print("PnL SUMMARY")
        print("="*60)
        print(f"\n💰 ACCOUNT")
        print(f"  Initial Balance:  ${summary['initial_balance']:>12,.2f}")
        print(f"  Current Equity:   ${summary['current_equity']:>12,.2f}")
        print(f"  Total Return:     ${summary['total_return']:>12,.2f}  ({summary['total_return_pct']:>6.2f}%)")
        print(f"\n📊 PnL BREAKDOWN")
        print(f"  Realized PnL:     ${summary['realized_pnl']:>12,.2f}")
        print(f"  Unrealized PnL:   ${summary['unrealized_pnl']:>12,.2f}")
        print(f"\n📅 TODAY")
        print(f"  Daily PnL:        ${daily['daily_pnl']:>12,.2f}  ({daily['daily_pnl_pct']:>6.2f}%)")
        print(f"  Daily High:       ${daily['daily_high']:>12,.2f}")
        print(f"  Daily Low:        ${daily['daily_low']:>12,.2f}")
        print("="*60 + "\n")

    def _reset_daily_tracking(self, current_equity: float):
        """Reset daily PnL tracking for new day."""
        self.daily_start_balance = current_equity
        self.daily_start_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        logger.info(f"Daily PnL tracking reset: start_balance=${current_equity:,.2f}")


# Example usage
def main():
    tracker = PnLTracker(initial_balance=10000.0)

    # Simulate some snapshots
    import time

    # Initial snapshot
    tracker.record_snapshot(
        account_balance=10000.0,
        position_value=0.0,
        unrealized_pnl=0.0,
        realized_pnl_since_start=0.0
    )

    # After a profitable trade
    time.sleep(1)
    tracker.record_snapshot(
        account_balance=9500.0,
        position_value=700.0,
        unrealized_pnl=200.0,
        realized_pnl_since_start=0.0
    )

    # After closing with profit
    time.sleep(1)
    tracker.record_snapshot(
        account_balance=10200.0,
        position_value=0.0,
        unrealized_pnl=0.0,
        realized_pnl_since_start=200.0
    )

    # Print summary
    tracker.print_summary()

    # Get equity curve
    equity_curve = tracker.get_equity_curve()
    print("Equity Curve:")
    print(equity_curve)


if __name__ == "__main__":
    main()
