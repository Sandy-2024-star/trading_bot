"""
Paper trading broker for simulation and testing.
Simulates order execution without real money.
"""

import uuid
from typing import Optional, List, Dict
from datetime import datetime
from loguru import logger

from core.base_broker import (
    BaseBroker, Order, Trade, OrderStatus, OrderSide, OrderType
)
from execution.repositories.order_repository import OrderRepository
from execution.repositories.trade_repository import TradeRepository


class PaperBroker(BaseBroker):
    """
    Paper trading broker that simulates order execution.

    Features:
    - Instant market order fills at current price
    - Simulated limit order execution
    - Stop loss/take profit simulation
    - Configurable fees and slippage
    - Position tracking
    - Optional database persistence via repositories
    """

    def __init__(
        self,
        initial_balance: float = 10000.0,
        fee_percent: float = 0.001,  # 0.1% fee
        slippage_percent: float = 0.0005,  # 0.05% slippage
        name: str = "PaperBroker",
        order_repository: Optional[OrderRepository] = None,
        trade_repository: Optional[TradeRepository] = None
    ):
        super().__init__(name)
        self.initial_balance = initial_balance
        self.account_balance = initial_balance
        self.fee_percent = fee_percent
        self.slippage_percent = slippage_percent
        self.current_prices: Dict[str, float] = {}
        self.position_costs: Dict[str, float] = {}
        self.connected = False
        
        # Persistence
        self.order_repo = order_repository
        self.trade_repo = trade_repository

        logger.info(
            f"PaperBroker initialized with ${initial_balance:,.2f}, "
            f"fees={fee_percent*100}%, slippage={slippage_percent*100}%"
        )

    async def connect(self):
        """Connect to paper broker (instant)."""
        self.connected = True
        logger.info("Paper broker connected")

    async def disconnect(self):
        """Disconnect from paper broker."""
        self.connected = False
        logger.info("Paper broker disconnected")

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
        Place an order in paper trading.

        Market orders are filled immediately.
        Limit/stop orders are stored and checked on price updates.
        """
        order_id = str(uuid.uuid4())[:8]

        order = Order(
            order_id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            status=OrderStatus.PENDING
        )

        self.orders[order_id] = order
        logger.info(f"Order placed: {order}")

        # Persist to DB if repository is available
        if self.order_repo:
            self.order_repo.save(order)

        # Execute market orders immediately
        if order_type == OrderType.MARKET:
            await self._execute_market_order(order)
        else:
            order.status = OrderStatus.OPEN
            logger.info(f"Limit/stop order opened: {order_id}")

        return order

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order."""
        order = self.orders.get(order_id)
        if not order:
            logger.warning(f"Order {order_id} not found")
            return False

        if not order.is_active():
            logger.warning(f"Order {order_id} is not active")
            return False

        order.cancel()
        
        # Persist cancellation if repository is available
        if self.order_repo:
            self.order_repo.save(order)
            
        logger.info(f"Order cancelled: {order_id}")
        return True

    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID."""
        return self.orders.get(order_id)

    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get all open orders."""
        open_orders = [o for o in self.orders.values() if o.is_active()]
        if symbol:
            open_orders = [o for o in open_orders if o.symbol == symbol]
        return open_orders

    async def get_account_balance(self) -> float:
        """Get current account balance."""
        return self.account_balance

    async def get_position(self, symbol: str) -> float:
        """Get position size for symbol."""
        return self.positions.get(symbol, 0.0)

    async def get_current_price(self, symbol: str) -> float:
        """Get current market price."""
        return self.current_prices.get(symbol, 0.0)

    async def update_price(self, symbol: str, price: float):
        """
        Update current market price and check for limit/stop order triggers.

        Args:
            symbol: Trading symbol
            price: Current market price
        """
        self.current_prices[symbol] = price

        # Check if any limit/stop orders should be triggered
        open_orders = await self.get_open_orders(symbol)
        for order in open_orders:
            await self._check_order_trigger(order, price)

    async def _execute_market_order(self, order: Order):
        """Execute a market order immediately."""
        current_price = self.current_prices.get(order.symbol, 0.0)
        if current_price == 0.0:
            logger.error(f"No price available for {order.symbol}")
            order.status = OrderStatus.REJECTED
            order.notes = "No price available"
            return

        # Apply slippage
        if order.side == OrderSide.BUY:
            fill_price = current_price * (1 + self.slippage_percent)
        else:
            fill_price = current_price * (1 - self.slippage_percent)

        # Calculate cost and fees
        cost = order.quantity * fill_price
        fees = cost * self.fee_percent

        # Check if we have sufficient balance (for buys)
        if order.side == OrderSide.BUY:
            total_cost = cost + fees
            if total_cost > self.account_balance:
                logger.error(f"Insufficient balance: need ${total_cost:.2f}, have ${self.account_balance:.2f}")
                order.status = OrderStatus.REJECTED
                order.notes = "Insufficient balance"
                return

            self.account_balance -= total_cost
            self.positions[order.symbol] = self.positions.get(order.symbol, 0.0) + order.quantity
            self.position_costs[order.symbol] = self.position_costs.get(order.symbol, 0.0) + total_cost

        else:  # SELL
            current_position = self.positions.get(order.symbol, 0.0)
            if order.quantity > current_position:
                logger.error(f"Insufficient position: need {order.quantity}, have {current_position}")
                order.status = OrderStatus.REJECTED
                order.notes = "Insufficient position"
                return

            avg_cost_per_unit = self.position_costs.get(order.symbol, 0.0) / current_position if current_position > 0 else 0.0
            realized_cost = avg_cost_per_unit * order.quantity
            realized_pnl = (fill_price * order.quantity) - realized_cost - fees

            self.account_balance += cost - fees
            remaining_position = current_position - order.quantity
            self.positions[order.symbol] = remaining_position
            if remaining_position > 0:
                self.position_costs[order.symbol] = avg_cost_per_unit * remaining_position
            else:
                self.position_costs.pop(order.symbol, None)

        # Fill the order
        order.fill(order.quantity, fill_price, fees)

        # Update persisted order if repository is available
        if self.order_repo:
            self.order_repo.save(order)

        # Create trade record
        trade = Trade(
            trade_id=str(uuid.uuid4())[:8],
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=fill_price,
            fees=fees,
            timestamp=datetime.now(),
            pnl=0.0
        )
        if order.side == OrderSide.SELL:
            trade.pnl = realized_pnl
        self.trades.append(trade)

        # Persist trade if repository is available
        if self.trade_repo:
            self.trade_repo.save(trade)

        logger.info(f"Market order filled: {order.order_id} at ${fill_price:.2f}")
        logger.info(f"Account balance: ${self.account_balance:.2f}")

    async def _check_order_trigger(self, order: Order, current_price: float):
        """Check if a limit/stop order should be triggered."""
        triggered = False

        if order.order_type == OrderType.LIMIT:
            if order.side == OrderSide.BUY and current_price <= order.price:
                triggered = True
            elif order.side == OrderSide.SELL and current_price >= order.price:
                triggered = True

        elif order.order_type == OrderType.STOP_LOSS:
            if order.side == OrderSide.BUY and current_price >= order.stop_price:
                triggered = True
            elif order.side == OrderSide.SELL and current_price <= order.stop_price:
                triggered = True

        elif order.order_type == OrderType.TAKE_PROFIT:
            if order.side == OrderSide.BUY and current_price >= order.price:
                triggered = True
            elif order.side == OrderSide.SELL and current_price <= order.price:
                triggered = True

        if triggered:
            logger.info(f"Order triggered: {order.order_id} at ${current_price:.2f}")
            # Convert to market order and execute
            order.order_type = OrderType.MARKET
            await self._execute_market_order(order)

    def calculate_position_pnl(self, symbol: str, current_price: float) -> float:
        """
        Calculate unrealized PnL for a position.

        Args:
            symbol: Trading symbol
            current_price: Current market price

        Returns:
            Unrealized PnL
        """
        position = self.positions.get(symbol, 0.0)
        if position == 0:
            return 0.0

        # Find entry price from trades
        symbol_trades = [t for t in self.trades if t.symbol == symbol]
        if not symbol_trades:
            return 0.0

        # Calculate average entry price
        total_qty = sum(t.quantity if t.side == OrderSide.BUY else -t.quantity for t in symbol_trades)
        total_cost = sum(
            t.quantity * t.price if t.side == OrderSide.BUY else -t.quantity * t.price
            for t in symbol_trades
        )

        if total_qty == 0:
            return 0.0

        avg_entry_price = total_cost / total_qty
        unrealized_pnl = (current_price - avg_entry_price) * position

        return unrealized_pnl

    def get_portfolio_value(self) -> float:
        """
        Calculate total portfolio value (cash + positions).

        Returns:
            Total portfolio value
        """
        portfolio_value = self.account_balance

        for symbol, quantity in self.positions.items():
            if quantity != 0:
                current_price = self.current_prices.get(symbol, 0.0)
                portfolio_value += quantity * current_price

        return portfolio_value

    def reset(self, initial_balance: Optional[float] = None):
        """
        Reset the paper broker to initial state.

        Args:
            initial_balance: New initial balance (optional)
        """
        if initial_balance:
            self.initial_balance = initial_balance

        self.account_balance = self.initial_balance
        self.orders.clear()
        self.trades.clear()
        self.positions.clear()
        self.position_costs.clear()
        self.current_prices.clear()

        logger.info(f"Paper broker reset to ${self.initial_balance:,.2f}")


# Example usage
async def main():
    broker = PaperBroker(initial_balance=10000.0)
    await broker.connect()

    # Set current price
    await broker.update_price("BTCUSD", 50000.0)

    # Place a market buy order
    order = await broker.place_order(
        symbol="BTCUSD",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=0.1
    )

    print(f"Order: {order}")
    print(f"Balance: ${await broker.get_account_balance():,.2f}")
    print(f"Position: {await broker.get_position('BTCUSD')}")

    # Update price and check PnL
    await broker.update_price("BTCUSD", 52000.0)
    pnl = broker.calculate_position_pnl("BTCUSD", 52000.0)
    print(f"Unrealized PnL: ${pnl:.2f}")
    print(f"Portfolio Value: ${broker.get_portfolio_value():,.2f}")

    # Get statistics
    stats = broker.get_statistics()
    print(f"Statistics: {stats}")

    await broker.disconnect()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
