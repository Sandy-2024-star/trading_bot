"""
Base strategy class for trading strategies.
All trading strategies should inherit from BaseStrategy.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, List, Union
from datetime import datetime
from enum import Enum
import pandas as pd
from loguru import logger


class OrderSide(Enum):
    """Order side enumeration."""
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


class Position:
    """Represents a trading position."""

    def __init__(
        self,
        symbol: str,
        side: OrderSide,
        size: float,
        entry_price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        timestamp: Optional[datetime] = None
    ):
        self.symbol = symbol
        self.side = side
        self.size = size
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.timestamp = timestamp or datetime.now()
        self.highest_price = entry_price  # For trailing stops
        self.exit_price: Optional[float] = None
        self.exit_timestamp: Optional[datetime] = None
        self.is_open = True

    def calculate_pnl(self, current_price: float) -> float:
        """
        Calculate profit/loss for the position.

        Args:
            current_price: Current market price

        Returns:
            PnL value (positive for profit, negative for loss)
        """
        if self.side == OrderSide.BUY:
            return (current_price - self.entry_price) * self.size
        else:  # SELL
            return (self.entry_price - current_price) * self.size

    def calculate_pnl_percent(self, current_price: float) -> float:
        """
        Calculate profit/loss percentage.

        Args:
            current_price: Current market price

        Returns:
            PnL percentage
        """
        if self.side == OrderSide.BUY:
            return ((current_price - self.entry_price) / self.entry_price) * 100
        else:  # SELL
            return ((self.entry_price - current_price) / self.entry_price) * 100

    def close(self, exit_price: float):
        """Close the position."""
        self.exit_price = exit_price
        self.exit_timestamp = datetime.now()
        self.is_open = False
        pnl = self.calculate_pnl(exit_price)
        logger.info(f"Position closed: {self.symbol} {self.side.value} at {exit_price}, PnL: {pnl:.2f}")

    def __repr__(self):
        return f"Position({self.symbol}, {self.side.value}, size={self.size}, entry={self.entry_price})"


class Signal:
    """Trading signal representation."""

    def __init__(
        self,
        symbol: str,
        side: OrderSide,
        strength: float,
        indicators: Dict,
        timestamp: Optional[datetime] = None,
        multi_leg: Optional[List[Dict]] = None
    ):
        self.symbol = symbol
        self.side = side
        self.strength = strength  # -1.0 to 1.0
        self.indicators = indicators
        self.timestamp = timestamp or datetime.now()
        self.multi_leg = multi_leg # Optional list of {'symbol': str, 'side': OrderSide}

    def __repr__(self):
        legs = f", legs={len(self.multi_leg)}" if self.multi_leg else ""
        return f"Signal({self.symbol}, {self.side.value}, strength={self.strength:.2f}{legs})"


class BaseStrategy(ABC):
    """
    Abstract base class for trading strategies.

    All custom strategies should inherit from this class and implement:
    - analyze(): Analyze market data and return signals
    - should_enter(): Determine if we should enter a position
    - should_exit(): Determine if we should exit a position
    """

    def __init__(self, name: str):
        self.name = name
        self.positions: List[Position] = []
        self.closed_positions: List[Position] = []
        self.market_context: Dict[str, Dict] = {}
        self.latest_signals: Dict[str, Optional[Signal]] = {}
        logger.info(f"Strategy '{name}' initialized")

    @abstractmethod
    def analyze(self, data: Union[pd.DataFrame, Dict[str, pd.DataFrame]]) -> Optional[Signal]:
        """
        Analyze market data and generate trading signal.

        Args:
            data: Either a single DataFrame with OHLCV data,
                  or a Dict mapping timeframe (e.g. '5m', '1h') to DataFrames.

        Returns:
            Signal object or None
        """
        pass


    @abstractmethod
    def should_enter(self, signal: Signal, current_price: float, account_balance: float) -> bool:
        """
        Determine if we should enter a position based on the signal.

        Args:
            signal: Trading signal
            current_price: Current market price
            account_balance: Available account balance

        Returns:
            True if should enter, False otherwise
        """
        pass

    @abstractmethod
    def should_exit(self, position: Position, current_price: float, data: pd.DataFrame) -> bool:
        """
        Determine if we should exit an open position.

        Args:
            position: Current position
            current_price: Current market price
            data: Recent market data

        Returns:
            True if should exit, False otherwise
        """
        pass

    def get_open_positions(self, symbol: Optional[str] = None) -> List[Position]:
        """Get all open positions, optionally filtered by symbol."""
        if symbol:
            return [p for p in self.positions if p.is_open and p.symbol == symbol]
        return [p for p in self.positions if p.is_open]

    def get_closed_positions(self) -> List[Position]:
        """Get all closed positions."""
        return self.closed_positions

    def add_position(self, position: Position):
        """Add a new position."""
        self.positions.append(position)
        logger.info(f"Position opened: {position}")

    def close_position(self, position: Position, exit_price: float):
        """Close a position."""
        position.close(exit_price)
        self.closed_positions.append(position)
        logger.info(f"Position closed with PnL: {position.calculate_pnl(exit_price):.2f}")

    def calculate_total_pnl(self, current_prices: Dict[str, float]) -> float:
        """
        Calculate total PnL across all positions.

        Args:
            current_prices: Dict mapping symbol to current price

        Returns:
            Total PnL
        """
        total_pnl = 0.0

        # Open positions
        for position in self.get_open_positions():
            if position.symbol in current_prices:
                total_pnl += position.calculate_pnl(current_prices[position.symbol])

        # Closed positions
        for position in self.closed_positions:
            if position.exit_price:
                total_pnl += position.calculate_pnl(position.exit_price)

        return total_pnl

    def get_position_count(self) -> int:
        """Get count of open positions."""
        return len(self.get_open_positions())

    def update_market_context(self, symbol: str, context: Dict):
        """Store non-price context such as sentiment or macro inputs for a symbol."""
        self.market_context[symbol] = context

    def get_market_context(self, symbol: Optional[str] = None):
        """Get context for one symbol or the full context map."""
        if symbol is not None:
            return self.market_context.get(symbol, {})
        return self.market_context.copy()

    def record_latest_signal(self, symbol: str, signal: Optional[Signal]):
        """Track the latest generated signal for dashboard visibility."""
        self.latest_signals[symbol] = signal

    def get_latest_signal(self, symbol: Optional[str] = None):
        """Get the latest signal for one symbol or all symbols."""
        if symbol is not None:
            return self.latest_signals.get(symbol)
        return self.latest_signals.copy()

    def get_stats(self) -> Dict:
        """Get strategy statistics."""
        closed = self.closed_positions
        if not closed:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0
            }

        winning_trades = [p for p in closed if p.exit_price and p.calculate_pnl(p.exit_price) > 0]
        losing_trades = [p for p in closed if p.exit_price and p.calculate_pnl(p.exit_price) <= 0]
        total_pnl = sum(p.calculate_pnl(p.exit_price) for p in closed if p.exit_price)

        return {
            "total_trades": len(closed),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": len(winning_trades) / len(closed) * 100 if closed else 0.0,
            "total_pnl": total_pnl
        }
