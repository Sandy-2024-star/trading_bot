"""
Circuit breaker for risk management.
Prevents trading when risk limits are breached.
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from enum import Enum
from loguru import logger


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation, trading allowed
    OPEN = "open"  # Circuit tripped, trading blocked
    HALF_OPEN = "half_open"  # Testing if conditions improved


class CircuitBreaker:
    """
    Risk management circuit breaker.

    Automatically stops trading when:
    - Daily loss limit exceeded
    - Maximum number of consecutive losses
    - Drawdown limit exceeded
    - Too many open positions
    - Daily trade limit exceeded
    """

    def __init__(
        self,
        max_daily_loss_percent: float = 0.05,  # 5% max daily loss
        max_consecutive_losses: int = 3,  # Stop after 3 losses in a row
        max_drawdown_percent: float = 0.15,  # 15% max drawdown
        max_open_positions: int = 5,  # Max 5 concurrent positions
        max_daily_trades: int = 20,  # Max 20 trades per day
        cooldown_minutes: int = 60  # 60 min cooldown after trip
    ):
        self.max_daily_loss_percent = max_daily_loss_percent
        self.max_consecutive_losses = max_consecutive_losses
        self.max_drawdown_percent = max_drawdown_percent
        self.max_open_positions = max_open_positions
        self.max_daily_trades = max_daily_trades
        self.cooldown_minutes = cooldown_minutes

        # State tracking
        self.state = CircuitBreakerState.CLOSED
        self.trip_reason: Optional[str] = None
        self.trip_time: Optional[datetime] = None
        self.consecutive_losses = 0
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.peak_balance = 0.0
        self.last_reset = datetime.now()

        logger.info("CircuitBreaker initialized")
        logger.info(f"Max daily loss: {max_daily_loss_percent*100}%")
        logger.info(f"Max consecutive losses: {max_consecutive_losses}")
        logger.info(f"Max drawdown: {max_drawdown_percent*100}%")

    def check(
        self,
        account_balance: float,
        open_position_count: int,
        recent_trades: List[Dict]
    ) -> bool:
        """
        Check if trading should be allowed.

        Args:
            account_balance: Current account balance
            open_position_count: Number of open positions
            recent_trades: List of recent trade results

        Returns:
            True if trading allowed, False if blocked
        """
        # Reset daily counters if new day
        self._reset_daily_if_needed()

        # Check if cooldown period has passed
        if self.state == CircuitBreakerState.OPEN:
            if self._cooldown_expired():
                logger.info("Cooldown period expired, moving to HALF_OPEN")
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                logger.warning(f"Circuit breaker OPEN: {self.trip_reason}")
                return False

        # Update peak balance for drawdown calculation
        if account_balance > self.peak_balance:
            self.peak_balance = account_balance

        # Check all circuit breaker conditions
        checks = [
            self._check_daily_loss(account_balance),
            self._check_consecutive_losses(),
            self._check_drawdown(account_balance),
            self._check_position_limit(open_position_count),
            self._check_daily_trade_limit()
        ]

        # If any check fails, trip the breaker
        if not all(checks):
            if self.state == CircuitBreakerState.CLOSED:
                self._trip()
            return False

        # If in HALF_OPEN and checks pass, reset to CLOSED
        if self.state == CircuitBreakerState.HALF_OPEN:
            logger.info("Conditions improved, circuit breaker CLOSED")
            self.state = CircuitBreakerState.CLOSED
            self.trip_reason = None

        return True

    def record_trade(self, pnl: float):
        """
        Record a completed trade.

        Args:
            pnl: Profit/loss from the trade
        """
        self.daily_trades += 1
        self.daily_pnl += pnl

        # Track consecutive losses
        if pnl < 0:
            self.consecutive_losses += 1
            logger.debug(f"Consecutive losses: {self.consecutive_losses}")
        else:
            self.consecutive_losses = 0

        logger.info(f"Trade recorded: PnL=${pnl:.2f}, Daily PnL=${self.daily_pnl:.2f}, Trades today={self.daily_trades}")

    def reset(self):
        """Manually reset the circuit breaker."""
        self.state = CircuitBreakerState.CLOSED
        self.trip_reason = None
        self.trip_time = None
        self.consecutive_losses = 0
        logger.info("Circuit breaker manually reset")

    def force_trip(self, reason: str):
        """Manually trip the circuit breaker."""
        self.trip_reason = reason
        self._trip()

    def get_status(self) -> Dict:
        """Get current circuit breaker status."""
        return {
            "state": self.state.value,
            "trip_reason": self.trip_reason,
            "consecutive_losses": self.consecutive_losses,
            "daily_trades": self.daily_trades,
            "daily_pnl": self.daily_pnl,
            "cooldown_remaining": self._cooldown_remaining_minutes()
        }

    def _check_daily_loss(self, account_balance: float) -> bool:
        """Check if daily loss limit exceeded."""
        if account_balance == 0:
            return True

        daily_loss_percent = abs(self.daily_pnl) / account_balance if self.daily_pnl < 0 else 0

        if daily_loss_percent > self.max_daily_loss_percent:
            self.trip_reason = f"Daily loss limit exceeded: {daily_loss_percent*100:.1f}%"
            logger.error(self.trip_reason)
            return False

        return True

    def _check_consecutive_losses(self) -> bool:
        """Check if consecutive loss limit exceeded."""
        if self.consecutive_losses >= self.max_consecutive_losses:
            self.trip_reason = f"Consecutive losses: {self.consecutive_losses}"
            logger.error(self.trip_reason)
            return False

        return True

    def _check_drawdown(self, account_balance: float) -> bool:
        """Check if drawdown limit exceeded."""
        if self.peak_balance == 0:
            return True

        drawdown = (self.peak_balance - account_balance) / self.peak_balance

        if drawdown > self.max_drawdown_percent:
            self.trip_reason = f"Drawdown limit exceeded: {drawdown*100:.1f}%"
            logger.error(self.trip_reason)
            return False

        return True

    def _check_position_limit(self, open_position_count: int) -> bool:
        """Check if position limit exceeded."""
        if open_position_count >= self.max_open_positions:
            self.trip_reason = f"Position limit reached: {open_position_count}/{self.max_open_positions}"
            logger.warning(self.trip_reason)
            return False

        return True

    def _check_daily_trade_limit(self) -> bool:
        """Check if daily trade limit exceeded."""
        if self.daily_trades >= self.max_daily_trades:
            self.trip_reason = f"Daily trade limit reached: {self.daily_trades}/{self.max_daily_trades}"
            logger.warning(self.trip_reason)
            return False

        return True

    def _trip(self):
        """Trip the circuit breaker."""
        self.state = CircuitBreakerState.OPEN
        self.trip_time = datetime.now()
        logger.error(f"🚨 CIRCUIT BREAKER TRIPPED: {self.trip_reason}")

    def _cooldown_expired(self) -> bool:
        """Check if cooldown period has expired."""
        if not self.trip_time:
            return True

        elapsed = datetime.now() - self.trip_time
        return elapsed.total_seconds() > (self.cooldown_minutes * 60)

    def _cooldown_remaining_minutes(self) -> int:
        """Get remaining cooldown time in minutes."""
        if not self.trip_time or self.state != CircuitBreakerState.OPEN:
            return 0

        elapsed = datetime.now() - self.trip_time
        elapsed_minutes = elapsed.total_seconds() / 60
        remaining = max(0, self.cooldown_minutes - elapsed_minutes)
        return int(remaining)

    def _reset_daily_if_needed(self):
        """Reset daily counters if it's a new day."""
        now = datetime.now()
        if now.date() > self.last_reset.date():
            logger.info("New trading day, resetting daily counters")
            self.daily_trades = 0
            self.daily_pnl = 0.0
            self.last_reset = now

            # If circuit was tripped yesterday, reset it
            if self.state == CircuitBreakerState.OPEN:
                logger.info("New day, resetting circuit breaker")
                self.reset()


class RiskManager:
    """
    Combined risk management system.
    Integrates position sizing, stop loss, and circuit breaker.
    """

    def __init__(self, circuit_breaker: CircuitBreaker):
        self.circuit_breaker = circuit_breaker
        logger.info("RiskManager initialized")

    def can_trade(
        self,
        account_balance: float,
        open_position_count: int,
        recent_trades: List[Dict]
    ) -> bool:
        """Check if trading is allowed."""
        return self.circuit_breaker.check(account_balance, open_position_count, recent_trades)

    def record_trade_result(self, pnl: float):
        """Record a trade result."""
        self.circuit_breaker.record_trade(pnl)

    def get_risk_status(self) -> Dict:
        """Get comprehensive risk status."""
        return {
            "circuit_breaker": self.circuit_breaker.get_status(),
            "trading_allowed": self.circuit_breaker.state == CircuitBreakerState.CLOSED
        }


# Example usage
def main():
    breaker = CircuitBreaker(
        max_daily_loss_percent=0.05,
        max_consecutive_losses=3,
        max_drawdown_percent=0.15,
        max_open_positions=5,
        max_daily_trades=20,
        cooldown_minutes=60
    )

    account_balance = 10000
    open_positions = 2
    recent_trades = []

    # Check if trading allowed
    can_trade = breaker.check(account_balance, open_positions, recent_trades)
    print(f"Can trade: {can_trade}")

    # Simulate losing trades
    for i in range(4):
        breaker.record_trade(-200)
        can_trade = breaker.check(account_balance, open_positions, recent_trades)
        print(f"After loss {i+1}, can trade: {can_trade}")

    # Get status
    status = breaker.get_status()
    print(f"\nStatus: {status}")


if __name__ == "__main__":
    main()
