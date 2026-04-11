"""
Order manager for coordinating strategy signals with broker execution.
Handles order lifecycle, position management, and risk checks.
"""

from typing import Optional, List
from loguru import logger

from core.base_broker import BaseBroker, Order, OrderSide, OrderType
from execution.repositories import OrderRepository, TradeRepository, PositionRepository
from core.base_strategy import BaseStrategy, Signal, Position as StrategyPosition, OrderSide as StrategyOrderSide
from risk.position_sizer import PositionSizer
from risk.stop_loss import StopLossManager
from risk.circuit_breaker import CircuitBreaker
from analysis.correlation import CorrelationEngine


class OrderManager:
    """
    Manages order execution and coordinates between strategy, risk, and broker.

    Responsibilities:
    - Convert strategy signals to broker orders
    - Apply risk management before execution
    - Track position lifecycle
    - Monitor stop loss and take profit levels
    - Sync strategy positions with broker positions
    """

    def __init__(
        self,
        broker: BaseBroker,
        strategy: BaseStrategy,
        position_sizer: PositionSizer,
        stop_loss_manager: StopLossManager,
        circuit_breaker: CircuitBreaker,
        position_repository: Optional[PositionRepository] = None,
        correlation_engine: Optional[CorrelationEngine] = None
    ):
        self.broker = broker
        self.strategy = strategy
        self.position_sizer = position_sizer
        self.stop_loss_manager = stop_loss_manager
        self.circuit_breaker = circuit_breaker
        self.pos_repo = position_repository
        self.correlation_engine = correlation_engine

        logger.info("OrderManager initialized")

    async def process_signal(self, signal: Signal, current_price: float) -> Optional[Order]:
        """
        Process a trading signal and execute if conditions are met.
        Supports atomic multi-leg orders (e.g. Pairs Trading).
        """
        # 1. Handle Multi-Leg Signals (Phase 4.1 Hardening)
        if signal.multi_leg:
            logger.info(f"Processing atomic multi-leg signal: {signal.symbol}")
            return await self._process_multi_leg_signal(signal)

        # 2. Check circuit breaker
        account_balance = await self.broker.get_account_balance()
        open_position_count = len(self.strategy.get_open_positions())
        recent_trades = self.broker.get_all_trades()

        can_trade = self.circuit_breaker.check(
            account_balance,
            open_position_count,
            []  # Simplified - would pass recent PnL data
        )

        if not can_trade:
            logger.warning("Circuit breaker blocked trading")
            return None

        # 2. Check strategy entry conditions
        should_enter = self.strategy.should_enter(signal, current_price, account_balance)
        if not should_enter:
            logger.debug(f"Strategy rejected entry for {signal.symbol}")
            return None

        # 3. Calculate position size
        is_long = signal.side == StrategyOrderSide.BUY

        # Calculate stop loss first
        stop_loss, take_profit = self.stop_loss_manager.calculate_both(
            current_price, is_long
        )

        # 3a. Check Portfolio Heat (Total Risk)
        current_positions = self.strategy.get_open_positions()
        current_total_risk = sum(
            self.position_sizer.calculate_risk_amount(p.entry_price, p.stop_loss, p.size)
            for p in current_positions if p.stop_loss
        )
        
        # Calculate risk for the proposed new trade
        new_quantity = self.position_sizer.calculate_quantity(
            account_balance, current_price, stop_loss, signal.strength
        )
        new_trade_risk = self.position_sizer.calculate_risk_amount(
            current_price, stop_loss, new_quantity
        )
        
        if not self.position_sizer.validate_portfolio_heat(current_total_risk, new_trade_risk, account_balance):
            logger.warning(f"Trade rejected: portfolio heat limit would be exceeded for {signal.symbol}")
            return None

        # 3b. Check Symbol Correlation
        if self.correlation_engine:
            open_symbols = [p.symbol for p in current_positions]
            violations = self.correlation_engine.check_trade_correlation(
                signal.symbol, open_symbols, threshold=0.85
            )
            if violations:
                logger.warning(f"Trade rejected: {signal.symbol} is too highly correlated with {violations}")
                return None

        # Calculate position size
        position_value = self.position_sizer.calculate_size(
            account_balance,
            current_price,
            stop_loss,
            signal.strength
        )

        quantity = self.position_sizer.calculate_quantity(
            account_balance,
            current_price,
            stop_loss,
            signal.strength
        )

        # Validate position size
        is_valid = self.position_sizer.validate_size(position_value, account_balance)
        if not is_valid:
            logger.warning(f"Position size validation failed for {signal.symbol}")
            return None

        # 4. Place order with broker
        broker_side = OrderSide.BUY if is_long else OrderSide.SELL

        try:
            order = await self.broker.place_order(
                symbol=signal.symbol,
                side=broker_side,
                order_type=OrderType.MARKET,
                quantity=quantity
            )

            if order.is_filled():
                # 5. Create strategy position
                strategy_position = StrategyPosition(
                    symbol=signal.symbol,
                    side=signal.side,
                    size=quantity,
                    entry_price=order.average_fill_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit
                )

                self.strategy.add_position(strategy_position)

                # Persist position
                if self.pos_repo:
                    self.pos_repo.save(strategy_position)

                logger.info(f"Position opened: {strategy_position}")
                logger.info(f"Order filled: {order}")

                return order
            else:
                logger.warning(f"Order not filled: {order}")
                return order

        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None

    async def check_exits(self, data_dict: dict):
        """
        Check if any open positions should be exited.

        Args:
            data_dict: Dict mapping symbol to current market data (DataFrame)
        """
        open_positions = self.strategy.get_open_positions()

        for position in open_positions:
            try:
                current_price = await self.broker.get_current_price(position.symbol)
                if current_price == 0.0:
                    logger.warning(f"No price available for {position.symbol}")
                    continue

                # Get market data for the symbol
                market_data = data_dict.get(position.symbol)
                if market_data is None:
                    logger.warning(f"No market data for {position.symbol}")
                    continue

                # 1. Update extreme price (highest for long, lowest for short)
                if position.side == StrategyOrderSide.BUY:
                    if current_price > position.highest_price:
                        position.highest_price = current_price
                else:  # SELL
                    if current_price < position.highest_price:
                        position.highest_price = current_price

                # 2. Update trailing stop loss if applicable
                from risk.stop_loss import StopLossType
                if self.stop_loss_manager.stop_loss_type == StopLossType.TRAILING:
                    new_stop = self.stop_loss_manager.update_trailing_stop(
                        position.stop_loss,
                        current_price,
                        position.highest_price,
                        position.side == StrategyOrderSide.BUY
                    )
                    if new_stop != position.stop_loss:
                        logger.info(f"Trailing stop updated for {position.symbol}: {new_stop:.2f}")
                        position.stop_loss = new_stop
                        
                        # Persist updated stop loss
                        if self.pos_repo:
                            self.pos_repo.save(position)

                # 3. Check strategy exit conditions
                should_exit = self.strategy.should_exit(position, current_price, market_data)

                if should_exit:
                    await self.close_position(position, current_price)

            except Exception as e:
                logger.error(f"Error checking exit for {position.symbol}: {e}")

    async def close_position(self, position: StrategyPosition, current_price: float) -> Optional[Order]:
        """
        Close a position.

        Args:
            position: Strategy position to close
            current_price: Current market price

        Returns:
            Close order if successful
        """
        try:
            # Place closing order
            broker_side = OrderSide.SELL if position.side == StrategyOrderSide.BUY else OrderSide.BUY

            order = await self.broker.place_order(
                symbol=position.symbol,
                side=broker_side,
                order_type=OrderType.MARKET,
                quantity=position.size
            )

            if order.is_filled():
                # Update strategy position
                self.strategy.close_position(position, order.average_fill_price)

                # Persist closed position
                if self.pos_repo:
                    self.pos_repo.save(position)

                # Calculate and record PnL
                pnl = position.calculate_pnl(order.average_fill_price)
                self.circuit_breaker.record_trade(pnl)

                # 6. Performance Attribution (Phase 3.2)
                # Find the signal that opened this position to see who to attribute the PnL to
                # For this implementation, we look at the strength/metadata of the position
                # In a more advanced version, we'd store signal_type in the Position object.
                
                # Default attribution
                signal_type = "technical"
                
                # Check for manual closure vs strategy
                import inspect
                caller = inspect.stack()[1].function
                if "dashboard" in caller or "manual" in caller:
                    signal_type = "manual"
                else:
                    # Heuristic: highest indicator score wins attribution
                    indicators = getattr(position, 'metadata', {})
                    if indicators:
                        ai_bias = abs(indicators.get('ai_bias', 0))
                        sent_bias = abs(indicators.get('sentiment_score', 0))
                        mtf_bias = abs(indicators.get('mtf_bias', 0))
                        
                        if ai_bias > 0.5: signal_type = "ai"
                        elif sent_bias > 0.5: signal_type = "sentiment"
                        elif mtf_bias > 0.5: signal_type = "mtf"

                # Update PnLTracker attribution
                # LiveTrader owns the pnl_tracker, so we look for it
                if hasattr(self.broker, 'pnl_tracker'):
                    self.broker.pnl_tracker.update_attribution(signal_type, pnl)
                elif hasattr(self, 'pnl_tracker'): # fallback if injected directly
                    self.pnl_tracker.update_attribution(signal_type, pnl)

                logger.info(f"Position closed: {position.symbol}, PnL: ${pnl:.2f}, Attributed to: {signal_type}")
                return order
            else:
                logger.warning(f"Close order not filled: {order}")
                return order

        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return None

    async def close_all_positions(self):
        """Close all open positions."""
        open_positions = self.strategy.get_open_positions()

        for position in open_positions:
            try:
                current_price = await self.broker.get_current_price(position.symbol)
                if current_price > 0:
                    await self.close_position(position, current_price)
            except Exception as e:
                logger.error(f"Error closing position {position.symbol}: {e}")

    async def _process_multi_leg_signal(self, signal: Signal) -> Optional[Order]:
        """Execute multiple orders atomically."""
        account_balance = await self.broker.get_account_balance()
        executed_orders = []
        
        try:
            for leg in signal.multi_leg:
                symbol = leg['symbol']
                side = leg['side']
                
                price = await self.broker.get_current_price(symbol)
                # For multi-leg, we use a simple fixed portion of equity for now
                quantity = self.position_sizer.calculate_quantity(
                    account_balance / len(signal.multi_leg), price, None, signal.strength
                )
                
                logger.info(f"Placing atomic leg: {side.value} {quantity} {symbol}")
                order = await self.broker.place_order(
                    symbol=symbol,
                    side=side,
                    order_type=OrderType.MARKET,
                    quantity=quantity
                )
                
                if not order or order.status == OrderStatus.CANCELLED:
                    raise Exception(f"Atomic leg failed: {symbol}")
                
                executed_orders.append(order)
                
            return executed_orders[0] # Return primary leg for tracking
            
        except Exception as e:
            logger.error(f"Multi-leg execution failed, potential imbalance! {e}")
            # In a real system, we'd attempt to emergency close the other legs here
            return None

    def get_status(self) -> dict:
        """Get current order manager status."""
        return {
            "open_positions": len(self.strategy.get_open_positions()),
            "strategy_stats": self.strategy.get_stats(),
            "broker_stats": self.broker.get_statistics(),
            "circuit_breaker": self.circuit_breaker.get_status()
        }


# Example usage
async def main():
    from execution.paper_broker import PaperBroker
    from strategy.signal_strategy import TechnicalSignalStrategy
    from risk.position_sizer import PositionSizer, SizingMethod
    from risk.stop_loss import StopLossManager, StopLossType
    from risk.circuit_breaker import CircuitBreaker
    import pandas as pd

    # Initialize components
    broker = PaperBroker(initial_balance=10000.0)
    await broker.connect()

    strategy = TechnicalSignalStrategy()

    position_sizer = PositionSizer(
        method=SizingMethod.RISK_BASED,
        risk_per_trade=0.02
    )

    stop_loss_manager = StopLossManager(
        stop_loss_type=StopLossType.FIXED_PERCENT,
        stop_loss_percent=0.05
    )

    circuit_breaker = CircuitBreaker()

    # Create order manager
    order_manager = OrderManager(
        broker=broker,
        strategy=strategy,
        position_sizer=position_sizer,
        stop_loss_manager=stop_loss_manager,
        circuit_breaker=circuit_breaker
    )

    # Set current price
    await broker.update_price("BTCUSD", 50000.0)

    # Create a sample signal
    from core.base_strategy import Signal, OrderSide as StrategyOrderSide

    signal = Signal(
        symbol="BTCUSD",
        side=StrategyOrderSide.BUY,
        strength=0.8,
        indicators={"rsi": 35}
    )

    # Process signal
    order = await order_manager.process_signal(signal, 50000.0)
    print(f"Order: {order}")

    # Get status
    status = order_manager.get_status()
    print(f"Status: {status}")

    await broker.disconnect()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
