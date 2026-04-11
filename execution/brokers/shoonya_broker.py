"""
Shoonya (Finvasia) broker implementation for real trade execution.
"""

import asyncio
from typing import Optional, List, Dict
from datetime import datetime
from loguru import logger
import pyotp
from NorenRestApiPy.NorenApi import NorenApi

from core.base_broker import BaseBroker, Order, Trade, OrderStatus, OrderSide, OrderType
from execution.repositories.order_repository import OrderRepository
from execution.repositories.trade_repository import TradeRepository
from config.config import config

class ShoonyaBroker(BaseBroker):
    """
    Shoonya API broker for real trade execution in Indian markets.
    """

    def __init__(
        self,
        order_repository: Optional[OrderRepository] = None,
        trade_repository: Optional[TradeRepository] = None,
        name: str = "ShoonyaBroker"
    ):
        super().__init__(name)
        self.api = NorenApi(host='https://api.shoonya.com/NorenWSTP/', websocket='wss://api.shoonya.com/NorenWSTP/')
        self.logged_in = False
        self.order_repo = order_repository
        self.trade_repo = trade_repository
        self.account_balance = 0.0
        logger.info(f"ShoonyaBroker initialized")

    async def connect(self):
        """Perform Shoonya login and session initialization."""
        if self.logged_in:
            return True

        try:
            totp = pyotp.TOTP(config.SHOONYA_TOTP_SECRET).now()
            login_resp = await asyncio.to_thread(
                self.api.login,
                userid=config.SHOONYA_USER_ID,
                password=config.SHOONYA_PASSWORD,
                twoFA=totp,
                vendor_code=config.SHOONYA_VENDOR_CODE,
                api_secret=config.SHOONYA_API_KEY,
                imei=config.SHOONYA_IMEI
            )

            if login_resp and login_resp.get('stat') == 'Ok':
                self.logged_in = True
                logger.info("ShoonyaBroker connected successfully")
                await self._update_balance()
                return True
            else:
                logger.error(f"ShoonyaBroker login failed: {login_resp}")
                return False
        except Exception as e:
            logger.error(f"Error connecting ShoonyaBroker: {e}")
            return False

    async def disconnect(self):
        """Logout from Shoonya."""
        if self.logged_in:
            await asyncio.to_thread(self.api.logout)
            self.logged_in = False
            logger.info("ShoonyaBroker disconnected")

    async def _update_balance(self):
        """Fetch current account balance/limits."""
        try:
            limits = await asyncio.to_thread(self.api.get_limits)
            if limits and limits.get('stat') == 'Ok':
                # 'cash' or 'marginused' are common fields
                self.account_balance = float(limits.get('cash', 0))
                logger.info(f"Shoonya account balance: {self.account_balance}")
        except Exception as e:
            logger.error(f"Error updating Shoonya balance: {e}")

    def _map_order_type(self, order_type: OrderType) -> str:
        """Map internal order types to Shoonya codes."""
        mapping = {
            OrderType.MARKET: 'MKT',
            OrderType.LIMIT: 'LMT',
            OrderType.STOP_LOSS: 'SL-LMT',
        }
        return mapping.get(order_type, 'MKT')

    def _map_side(self, side: OrderSide) -> str:
        """Map internal side to Shoonya side."""
        return 'B' if side == OrderSide.BUY else 'S'

    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        **kwargs
    ) -> Order:
        """Place an order via Shoonya API."""
        if not self.logged_in:
            await self.connect()

        # Symbol mapping (assume format EXCHANGE|SYMBOL)
        if "|" not in symbol:
            # Default logic: If it looks like an option, use NFO
            if any(opt in symbol.upper() for opt in ['CE', 'PE']) and len(symbol) > 10:
                symbol = f"NFO|{symbol}"
            else:
                symbol = f"NSE|{symbol}"
        
        exch, token_symbol = symbol.split('|')

        try:
            # Construct Shoonya order request
            # prctyp: LMT, MKT, SL-LMT, SL-MKT
            # product: C (Cash/CNC), M (Margin/NRML), I (Intraday/MIS)
            
            # Default product logic
            default_product = 'M' if exch == 'NFO' else 'C'
            product = kwargs.get('product', default_product)
            
            sh_order = await asyncio.to_thread(
                self.api.place_order,
                buy_or_sell=self._map_side(side),
                product_type=product,
                exchange=exch,
                tradingsymbol=token_symbol,
                quantity=int(quantity),
                discloseqty=0,
                price_type=self._map_order_type(order_type),
                price=price or 0,
                trigger_price=stop_price or 0,
                retention='DAY',
                remarks='TradingBot'
            )

            if sh_order and sh_order.get('stat') == 'Ok':
                noren_id = sh_order.get('norenordno')
                order = Order(
                    order_id=noren_id,
                    symbol=symbol,
                    side=side,
                    order_type=order_type,
                    quantity=quantity,
                    price=price,
                    stop_price=stop_price,
                    status=OrderStatus.OPEN,
                    created_at=datetime.now()
                )
                
                self.orders[noren_id] = order
                if self.order_repo:
                    self.order_repo.save(order)
                
                logger.info(f"Shoonya order placed: {noren_id}")
                return order
            else:
                raise Exception(f"Shoonya order placement failed: {sh_order}")

        except Exception as e:
            logger.error(f"Error placing Shoonya order: {e}")
            # Return a failed order object
            return Order(
                order_id=f"FAILED_{datetime.now().timestamp()}",
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                status=OrderStatus.CANCELLED,
                notes=str(e)
            )

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order on Shoonya."""
        try:
            resp = await asyncio.to_thread(self.api.cancel_order, norenordno=order_id)
            if resp and resp.get('stat') == 'Ok':
                if order_id in self.orders:
                    self.orders[order_id].status = OrderStatus.CANCELLED
                    if self.order_repo:
                        self.order_repo.save(self.orders[order_id])
                return True
            return False
        except Exception as e:
            logger.error(f"Error cancelling Shoonya order {order_id}: {e}")
            return False

    async def get_positions(self) -> List[Dict]:
        """Fetch current open positions from Shoonya."""
        try:
            pos = await asyncio.to_thread(self.api.get_positions)
            if pos and isinstance(pos, list):
                return pos
            return []
        except Exception as e:
            logger.error(f"Error fetching Shoonya positions: {e}")
            return []
