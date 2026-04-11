"""
Alert system for monitoring trading events and conditions.
"""

from enum import Enum
from typing import List, Callable, Optional, Dict
from datetime import datetime
from dataclasses import dataclass
from loguru import logger


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of alerts."""
    TRADE_EXECUTED = "trade_executed"
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"
    STOP_LOSS_HIT = "stop_loss_hit"
    TAKE_PROFIT_HIT = "take_profit_hit"
    CIRCUIT_BREAKER_TRIPPED = "circuit_breaker_tripped"
    DAILY_LOSS_LIMIT = "daily_loss_limit"
    LARGE_PROFIT = "large_profit"
    LARGE_LOSS = "large_loss"
    CONNECTION_ERROR = "connection_error"
    SYSTEM_ERROR = "system_error"
    LOW_BALANCE = "low_balance"
    HIGH_DRAWDOWN = "high_drawdown"


@dataclass
class Alert:
    """Represents an alert."""
    alert_type: AlertType
    level: AlertLevel
    message: str
    timestamp: datetime
    data: Dict = None

    def __post_init__(self):
        if self.data is None:
            self.data = {}

    def __str__(self):
        level_emoji = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.ERROR: "❌",
            AlertLevel.CRITICAL: "🚨"
        }
        emoji = level_emoji.get(self.level, "")
        return f"{emoji} [{self.level.value.upper()}] {self.message}"


class AlertManager:
    """
    Manages alerts and notifications.

    Features:
    - Multiple alert handlers (console, file, Telegram, etc.)
    - Alert filtering by level and type
    - Alert history
    - Customizable alert conditions
    """

    def __init__(self):
        self.handlers: List[Callable[[Alert], None]] = []
        self.alert_history: List[Alert] = []
        self.min_level = AlertLevel.INFO
        self.enabled = True

        # Alert thresholds
        self.large_profit_threshold = 500.0  # $500
        self.large_loss_threshold = -500.0   # -$500
        self.low_balance_threshold = 1000.0  # $1000
        self.high_drawdown_threshold = 0.15  # 15%

        logger.info("AlertManager initialized")

    def add_handler(self, handler: Callable[[Alert], None]):
        """
        Add an alert handler function.

        Args:
            handler: Function that takes an Alert and processes it
        """
        self.handlers.append(handler)
        logger.info(f"Alert handler added: {handler.__name__}")

    def remove_handler(self, handler: Callable[[Alert], None]):
        """Remove an alert handler."""
        if handler in self.handlers:
            self.handlers.remove(handler)
            logger.info(f"Alert handler removed: {handler.__name__}")

    def send_alert(
        self,
        alert_type: AlertType,
        level: AlertLevel,
        message: str,
        data: Optional[Dict] = None
    ):
        """
        Send an alert to all registered handlers.

        Args:
            alert_type: Type of alert
            level: Severity level
            message: Alert message
            data: Additional data
        """
        if not self.enabled:
            return

        # Check if alert level meets minimum threshold
        level_priority = {
            AlertLevel.INFO: 0,
            AlertLevel.WARNING: 1,
            AlertLevel.ERROR: 2,
            AlertLevel.CRITICAL: 3
        }

        if level_priority[level] < level_priority[self.min_level]:
            return

        alert = Alert(
            alert_type=alert_type,
            level=level,
            message=message,
            timestamp=datetime.now(),
            data=data or {}
        )

        # Store in history
        self.alert_history.append(alert)

        # Send to all handlers
        for handler in self.handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler {handler.__name__}: {e}")

        logger.debug(f"Alert sent: {alert}")

    # Convenience methods for common alerts

    def trade_executed(self, symbol: str, side: str, quantity: float, price: float, pnl: float = None):
        """Alert when a trade is executed."""
        message = f"Trade executed: {side.upper()} {quantity:.4f} {symbol} @ ${price:,.2f}"
        if pnl is not None:
            message += f" (PnL: ${pnl:,.2f})"

        self.send_alert(
            AlertType.TRADE_EXECUTED,
            AlertLevel.INFO,
            message,
            {"symbol": symbol, "side": side, "quantity": quantity, "price": price, "pnl": pnl}
        )

    def position_opened(self, symbol: str, side: str, size: float, entry_price: float, stop_loss: float, take_profit: float):
        """Alert when a position is opened."""
        message = f"Position opened: {side.upper()} {size:.4f} {symbol} @ ${entry_price:,.2f}"
        self.send_alert(
            AlertType.POSITION_OPENED,
            AlertLevel.INFO,
            message,
            {
                "symbol": symbol,
                "side": side,
                "size": size,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit
            }
        )

    def position_closed(self, symbol: str, side: str, size: float, entry_price: float, exit_price: float, pnl: float):
        """Alert when a position is closed."""
        pnl_pct = (pnl / (size * entry_price)) * 100 if size * entry_price > 0 else 0.0
        message = f"Position closed: {symbol} {side.upper()} @ ${exit_price:,.2f} - PnL: ${pnl:,.2f} ({pnl_pct:+.2f}%)"

        level = AlertLevel.INFO
        if pnl >= self.large_profit_threshold:
            level = AlertLevel.WARNING
            alert_type = AlertType.LARGE_PROFIT
        elif pnl <= self.large_loss_threshold:
            level = AlertLevel.ERROR
            alert_type = AlertType.LARGE_LOSS
        else:
            alert_type = AlertType.POSITION_CLOSED

        self.send_alert(
            alert_type,
            level,
            message,
            {
                "symbol": symbol,
                "side": side,
                "size": size,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "pnl": pnl,
                "pnl_pct": pnl_pct
            }
        )

    def stop_loss_hit(self, symbol: str, stop_price: float, pnl: float):
        """Alert when stop loss is triggered."""
        message = f"⛔ Stop loss hit: {symbol} @ ${stop_price:,.2f} - Loss: ${pnl:,.2f}"
        self.send_alert(
            AlertType.STOP_LOSS_HIT,
            AlertLevel.WARNING,
            message,
            {"symbol": symbol, "stop_price": stop_price, "pnl": pnl}
        )

    def take_profit_hit(self, symbol: str, take_profit_price: float, pnl: float):
        """Alert when take profit is triggered."""
        message = f"✅ Take profit hit: {symbol} @ ${take_profit_price:,.2f} - Profit: ${pnl:,.2f}"
        self.send_alert(
            AlertType.TAKE_PROFIT_HIT,
            AlertLevel.INFO,
            message,
            {"symbol": symbol, "take_profit_price": take_profit_price, "pnl": pnl}
        )

    def circuit_breaker_tripped(self, reason: str):
        """Alert when circuit breaker is triggered."""
        message = f"🚨 Circuit breaker tripped: {reason}"
        self.send_alert(
            AlertType.CIRCUIT_BREAKER_TRIPPED,
            AlertLevel.CRITICAL,
            message,
            {"reason": reason}
        )

    def daily_loss_limit(self, daily_loss: float, limit: float):
        """Alert when daily loss limit is reached."""
        message = f"📉 Daily loss limit reached: ${daily_loss:,.2f} (limit: ${limit:,.2f})"
        self.send_alert(
            AlertType.DAILY_LOSS_LIMIT,
            AlertLevel.CRITICAL,
            message,
            {"daily_loss": daily_loss, "limit": limit}
        )

    def low_balance(self, balance: float, threshold: float):
        """Alert when account balance is low."""
        message = f"💸 Low balance warning: ${balance:,.2f} (threshold: ${threshold:,.2f})"
        self.send_alert(
            AlertType.LOW_BALANCE,
            AlertLevel.WARNING,
            message,
            {"balance": balance, "threshold": threshold}
        )

    def high_drawdown(self, drawdown_pct: float, threshold_pct: float):
        """Alert when drawdown is high."""
        message = f"📊 High drawdown: {drawdown_pct:.2f}% (threshold: {threshold_pct:.2f}%)"
        self.send_alert(
            AlertType.HIGH_DRAWDOWN,
            AlertLevel.ERROR,
            message,
            {"drawdown_pct": drawdown_pct, "threshold_pct": threshold_pct}
        )

    def system_error(self, error_message: str):
        """Alert for system errors."""
        message = f"⚙️ System error: {error_message}"
        self.send_alert(
            AlertType.SYSTEM_ERROR,
            AlertLevel.ERROR,
            message,
            {"error": error_message}
        )

    def connection_error(self, service: str, error: str):
        """Alert for connection errors."""
        message = f"🔌 Connection error ({service}): {error}"
        self.send_alert(
            AlertType.CONNECTION_ERROR,
            AlertLevel.ERROR,
            message,
            {"service": service, "error": error}
        )

    def get_recent_alerts(self, count: int = 10) -> List[Alert]:
        """Get recent alerts."""
        return self.alert_history[-count:] if len(self.alert_history) >= count else self.alert_history

    def get_alerts_by_level(self, level: AlertLevel) -> List[Alert]:
        """Get all alerts of a specific level."""
        return [a for a in self.alert_history if a.level == level]

    def get_alerts_by_type(self, alert_type: AlertType) -> List[Alert]:
        """Get all alerts of a specific type."""
        return [a for a in self.alert_history if a.alert_type == alert_type]

    def clear_history(self):
        """Clear alert history."""
        self.alert_history.clear()
        logger.info("Alert history cleared")

    def enable(self):
        """Enable alerts."""
        self.enabled = True
        logger.info("Alerts enabled")

    def disable(self):
        """Disable alerts."""
        self.enabled = False
        logger.info("Alerts disabled")


# Built-in handlers

def console_handler(alert: Alert):
    """Print alerts to console."""
    print(f"[{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {alert}")


def file_handler(filepath: str):
    """Create a file handler for alerts."""
    def handler(alert: Alert):
        with open(filepath, 'a') as f:
            f.write(f"[{alert.timestamp}] [{alert.level.value}] [{alert.alert_type.value}] {alert.message}\n")
    return handler


# Example usage
def main():
    manager = AlertManager()

    # Add console handler
    manager.add_handler(console_handler)

    # Send some test alerts
    manager.position_opened("BTCUSD", "buy", 0.1, 50000.0, 47500.0, 52500.0)
    manager.trade_executed("BTCUSD", "buy", 0.1, 50000.0)
    manager.position_closed("BTCUSD", "buy", 0.1, 50000.0, 51000.0, 100.0)
    manager.large_profit_threshold = 50.0
    manager.position_closed("ETHERS", "sell", 1.0, 3000.0, 2900.0, 600.0)
    manager.circuit_breaker_tripped("3 consecutive losses")
    manager.system_error("API connection timeout")

    # Get recent alerts
    print("\nRecent alerts:")
    for alert in manager.get_recent_alerts(5):
        print(f"  - {alert}")


if __name__ == "__main__":
    main()
