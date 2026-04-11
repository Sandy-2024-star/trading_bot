"""
Base broker interface for order execution.
All broker implementations should inherit from BaseBroker.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from loguru import logger


class OrderStatus(Enum):
    """Order status enumeration."""
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class OrderSide(Enum):
    """Order side enumeration."""
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    STOP_LIMIT = "stop_limit"
    TAKE_PROFIT = "take_profit"


@dataclass
class Order:
    """Represents a trading order."""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None  # For limit orders
    stop_price: Optional[float] = None  # For stop orders
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    average_fill_price: float = 0.0
    created_at: datetime = None
    filled_at: Optional[datetime] = None
    fees: float = 0.0
    notes: str = ""

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    def is_filled(self) -> bool:
        """Check if order is fully filled."""
        return self.status == OrderStatus.FILLED

    def is_active(self) -> bool:
        """Check if order is active (pending or open)."""
        return self.status in [OrderStatus.PENDING, OrderStatus.OPEN]

    def fill(self, quantity: float, price: float, fees: float = 0.0):
        """Mark order as filled."""
        self.filled_quantity += quantity
        self.average_fill_price = (
            (self.average_fill_price * (self.filled_quantity - quantity) + price * quantity)
            / self.filled_quantity
        ) if self.filled_quantity > 0 else price
        self.fees += fees

        if self.filled_quantity >= self.quantity:
            self.status = OrderStatus.FILLED
            self.filled_at = datetime.now()
        else:
            self.status = OrderStatus.PARTIALLY_FILLED

    def cancel(self):
        """Cancel the order."""
        self.status = OrderStatus.CANCELLED

    def __repr__(self):
        return (
            f"Order({self.order_id}, {self.symbol}, {self.side.value}, "
            f"{self.order_type.value}, qty={self.quantity}, "
            f"status={self.status.value})"
        )


@dataclass
class Trade:
    """Represents a completed trade (filled order)."""
    trade_id: str
    order_id: str
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    fees: float
    timestamp: datetime
    pnl: float = 0.0

    def __repr__(self):
        return (
            f"Trade({self.trade_id}, {self.symbol}, {self.side.value}, "
            f"qty={self.quantity}, price={self.price})"
        )


class BaseBroker(ABC):
    """
    Abstract base class for broker implementations.

    All broker connectors (paper trading, live brokers) should inherit from this.
    """

    def __init__(self, name: str):
        self.name = name
        self.orders: Dict[str, Order] = {}
        self.trades: List[Trade] = []
        self.positions: Dict[str, float] = {}  # symbol -> quantity
        self.account_balance = 0.0
        self.initial_balance = 0.0
        logger.info(f"Broker '{name}' initialized")

    @abstractmethod
    async def connect(self):
        """Connect to the broker."""
        pass

    @abstractmethod
    async def disconnect(self):
        """Disconnect from the broker."""
        pass

    @abstractmethod
    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None
    ) -> Order:
        """
        Place an order.

        Args:
            symbol: Trading symbol
            side: BUY or SELL
            order_type: Order type (market, limit, etc.)
            quantity: Order quantity
            price: Limit price (for limit orders)
            stop_price: Stop price (for stop orders)

        Returns:
            Order object
        """
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.

        Args:
            order_id: Order ID to cancel

        Returns:
            True if cancelled successfully
        """
        pass

    @abstractmethod
    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get order details by ID."""
        pass

    @abstractmethod
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get all open orders, optionally filtered by symbol."""
        pass

    @abstractmethod
    async def get_account_balance(self) -> float:
        """Get current account balance."""
        pass

    @abstractmethod
    async def get_position(self, symbol: str) -> float:
        """Get current position size for a symbol."""
        pass

    @abstractmethod
    async def get_current_price(self, symbol: str) -> float:
        """Get current market price for a symbol."""
        pass

    def get_all_orders(self) -> List[Order]:
        """Get all orders (active and historical)."""
        return list(self.orders.values())

    def get_all_trades(self) -> List[Trade]:
        """Get all executed trades."""
        return self.trades

    def get_all_positions(self) -> Dict[str, float]:
        """Get all current positions."""
        return self.positions.copy()

    def calculate_total_pnl(self) -> float:
        """Calculate total PnL."""
        return sum(trade.pnl for trade in self.trades)

    def get_statistics(self) -> Dict:
        """Get broker statistics."""
        total_trades = len(self.trades)
        if total_trades == 0:
            return {
                "total_trades": 0,
                "total_pnl": 0.0,
                "win_rate": 0.0,
                "total_fees": 0.0,
                "account_balance": self.account_balance,
                "initial_balance": self.initial_balance,
                "return_pct": 0.0
            }

        total_pnl = self.calculate_total_pnl()
        total_fees = sum(trade.fees for trade in self.trades)
        winning_trades = [t for t in self.trades if t.pnl > 0]
        win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0.0
        return_pct = (
            ((self.account_balance - self.initial_balance) / self.initial_balance * 100)
            if self.initial_balance > 0 else 0.0
        )

        return {
            "total_trades": total_trades,
            "total_pnl": total_pnl,
            "win_rate": win_rate,
            "total_fees": total_fees,
            "account_balance": self.account_balance,
            "initial_balance": self.initial_balance,
            "return_pct": return_pct
        }
