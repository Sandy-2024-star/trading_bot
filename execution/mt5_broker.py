"""
MT5 broker implementation using open-source mt5_bridge.
Provides order execution through MetaTrader 5 using socket communication.

Requirements:
- MT5 running on Windows (VM or VPS)
- MT5SocketClient EA installed and configured
- Python server running (mt5_bridge.main)

Account: Sandesh P
Server: MetaQuotes-Demo
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from loguru import logger

from core.base_broker import (
    BaseBroker, Order, Trade, OrderStatus, OrderSide, OrderType
)


class MT5Broker(BaseBroker):
    """
    MT5 broker using open-source mt5_bridge socket connection.
    
    Features:
    - Market, limit, stop orders
    - Stop loss and take profit
    - Position tracking
    - Account balance management
    - Real-time price fetching
    
    Supported Markets:
    - Forex: EURUSD, GBPUSD, USDJPY, etc.
    - Commodities: XAUUSD, XAGUSD, etc.
    - Indices: US100, US30, etc.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 1111,
        name: str = "MT5Broker"
    ):
        super().__init__(name)
        self.host = host
        self.port = port
        self._bridge = None
        self._connected = False
        self._local_orders: Dict[str, Order] = {}
        logger.info(f"MT5Broker initialized for {host}:{port}")

    async def connect(self):
        """Connect to MT5 via mt5_bridge socket."""
        if self._connected:
            return

        try:
            import sys
            sys.path.insert(0, str(self.host))
            
            from mt5_bridge import MT5Bridge, Timeframe
            
            self._bridge = MT5Bridge(host=self.host, port=self.port)
            
            logger.info(f"Connecting to MT5 at {self.host}:{self.port}...")
            await self._bridge.start()
            await self._bridge.wait_for_connection(timeout=60)
            
            self._connected = True
            await self._sync_state()
            
            logger.info(f"MT5Broker connected successfully")
            
        except ImportError as e:
            logger.error("mt5_bridge not found. Install from ../mt5_third_parties/")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to MT5: {e}")
            raise

    async def _sync_state(self):
        """Synchronize local state with MT5 terminal state."""
        try:
            account = await self._bridge.get_account()
            self.account_balance = account.balance
            self.initial_balance = account.balance
            logger.debug(f"Synced account balance: ${self.account_balance:.2f}")
        except Exception as e:
            logger.error(f"Error syncing state: {e}")

    async def disconnect(self):
        """Disconnect from MT5 terminal."""
        if self._bridge and self._connected:
            await self._bridge.stop()
            self._connected = False
            logger.info("MT5Broker disconnected")

    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        comment: str = ""
    ) -> Order:
        """
        Place an order on MT5.
        
        Args:
            symbol: Trading symbol (e.g., EURUSD)
            side: BUY or SELL
            order_type: MARKET, LIMIT, STOP_LOSS, etc.
            quantity: Lot size
            price: Limit price (for limit orders)
            stop_price: Stop price (for stop orders)
            stop_loss: Stop loss price
            take_profit: Take profit price
            comment: Order comment
            
        Returns:
            Order object
        """
        if not self._connected:
            await self.connect()

        local_order_id = str(uuid.uuid4())[:8]
        
        order = Order(
            order_id=local_order_id,
            symbol=symbol.upper(),
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            status=OrderStatus.PENDING
        )
        
        self._local_orders[local_order_id] = order
        self.orders[local_order_id] = order
        
        try:
            if order_type == OrderType.MARKET:
                if side == OrderSide.BUY:
                    result = await self._bridge.buy(symbol, quantity, stop_loss, take_profit)
                else:
                    result = await self._bridge.sell(symbol, quantity, stop_loss, take_profit)
            elif order_type == OrderType.LIMIT:
                if side == OrderSide.BUY:
                    result = await self._bridge.buy_limit(symbol, quantity, price, stop_loss, take_profit)
                else:
                    result = await self._bridge.sell_limit(symbol, quantity, price, stop_loss, take_profit)
            elif order_type == OrderType.STOP_LOSS:
                if side == OrderSide.BUY:
                    result = await self._bridge.buy_stop(symbol, quantity, stop_price, stop_loss, take_profit)
                else:
                    result = await self._bridge.sell_stop(symbol, quantity, stop_price, stop_loss, take_profit)
            else:
                raise ValueError(f"Unsupported order type: {order_type}")

            order.status = OrderStatus.OPEN
            order.notes = f"Ticket: {result.ticket}"
            logger.info(f"Order placed on MT5: {order}")
            
        except Exception as e:
            order.status = OrderStatus.REJECTED
            order.notes = str(e)
            logger.error(f"Order rejected: {e}")
        
        return order

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order."""
        if not self._connected:
            await self.connect()

        order = self._local_orders.get(order_id) or self.orders.get(order_id)
        if not order:
            logger.warning(f"Order {order_id} not found")
            return False

        if not order.is_active():
            logger.warning(f"Order {order_id} is not active")
            return False

        try:
            await self._bridge.delete_order(order_id)
            order.cancel()
            logger.info(f"Order cancelled: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False

    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get order details by ID."""
        return self._local_orders.get(order_id) or self.orders.get(order_id)

    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get all open orders."""
        if not self._connected:
            await self.connect()

        open_orders = []
        for order in list(self._local_orders.values()) + list(self.orders.values()):
            if order.is_active():
                if symbol is None or order.symbol == symbol.upper():
                    open_orders.append(order)
        return open_orders

    async def get_account_balance(self) -> float:
        """Get current account balance."""
        if not self._connected:
            await self.connect()

        try:
            account = await self._bridge.get_account()
            self.account_balance = account.balance
            return self.account_balance
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return self.account_balance

    async def get_position(self, symbol: str) -> float:
        """Get current position size for a symbol."""
        if not self._connected:
            await self.connect()

        try:
            positions = await self._bridge.get_positions()
            for pos in positions:
                if pos.symbol.upper() == symbol.upper():
                    return pos.volume
            return 0.0
        except Exception as e:
            logger.error(f"Error fetching position for {symbol}: {e}")
            return self.positions.get(symbol.upper(), 0.0)

    async def get_current_price(self, symbol: str) -> float:
        """Get current market price for a symbol."""
        if not self._connected:
            await self.connect()

        try:
            tick = await self._bridge.get_tick(symbol)
            return tick.bid
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return 0.0

    async def close_position(
        self,
        symbol: str,
        volume: Optional[float] = None,
        comment: str = ""
    ) -> bool:
        """Close a position (fully or partially)."""
        if not self._connected:
            await self.connect()

        try:
            positions = await self._bridge.get_positions()
            for pos in positions:
                if pos.symbol.upper() == symbol.upper():
                    result = await self._bridge.close_position(pos.ticket)
                    logger.info(f"Position closed: {symbol}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return False

    async def modify_position(
        self,
        symbol: str,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> bool:
        """Modify position SL/TP."""
        if not self._connected:
            await self.connect()

        try:
            positions = await self._bridge.get_positions()
            for pos in positions:
                if pos.symbol.upper() == symbol.upper():
                    await self._bridge.modify_position(pos.ticket, stop_loss, take_profit)
                    logger.info(f"Position modified: {symbol}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error modifying position: {e}")
            return False

    def get_positions_summary(self) -> List[Dict]:
        """Get summary of all open positions."""
        if not self._connected:
            return []

        try:
            positions = asyncio.run(self._bridge.get_positions())
            summary = []
            for pos in positions:
                summary.append({
                    "ticket": pos.ticket,
                    "symbol": pos.symbol,
                    "order_type": pos.order_type,
                    "volume": pos.volume,
                    "profit": pos.profit,
                    "open_price": pos.open_price,
                    "current_price": pos.current_price,
                    "stop_loss": pos.stop_loss,
                    "take_profit": pos.take_profit,
                })
            return summary
        except Exception as e:
            logger.error(f"Error getting positions summary: {e}")
            return []


async def main():
    """Demo usage of MT5Broker."""
    import os
    
    host = os.getenv("MT5_BRIDGE_HOST", "127.0.0.1")
    port = int(os.getenv("MT5_BRIDGE_PORT", "1111"))

    print("\n" + "="*60)
    print("MT5 BROKER DEMO (mt5_bridge)")
    print("="*60)

    broker = MT5Broker(host=host, port=port)

    try:
        await broker.connect()

        print("\n[1] Account Info:")
        balance = await broker.get_account_balance()
        print(f"  Balance: ${balance:,.2f}")

        print("\n[2] Current Price:")
        price = await broker.get_current_price("EURUSD")
        print(f"  EURUSD: {price:.5f}")

        print("\n[3] Open Positions:")
        positions = broker.get_positions_summary()
        print(f"  Positions: {len(positions)}")
        for pos in positions:
            print(f"  - {pos['symbol']}: {pos['volume']} lots, PnL=${pos['profit']:.2f}")

        print("\n[4] MT5 Status:")
        print(f"  Connection: Active")
        print(f"  Ready for trading!")

    finally:
        await broker.disconnect()

    print("\n" + "="*60)
    print("MT5Broker ready for live trading!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
