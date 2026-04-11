"""
Backtesting engine for testing strategies on historical data.
"""

import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger

from execution.paper_broker import PaperBroker
from core.base_broker import OrderSide, OrderType
from core.base_strategy import BaseStrategy, Signal, Position, OrderSide as StrategyOrderSide
from risk.position_sizer import PositionSizer
from risk.stop_loss import StopLossManager
from risk.circuit_breaker import CircuitBreaker


class BacktestResult:
    """Stores backtest results and statistics."""

    def __init__(
        self,
        initial_balance: float,
        final_balance: float,
        trades: List,
        equity_curve: pd.DataFrame,
        strategy_name: str,
        start_date: datetime,
        end_date: datetime
    ):
        self.initial_balance = initial_balance
        self.final_balance = final_balance
        self.trades = trades
        self.equity_curve = equity_curve
        self.strategy_name = strategy_name
        self.start_date = start_date
        self.end_date = end_date

        # Calculate statistics
        self.calculate_statistics()

    def calculate_statistics(self):
        """Calculate backtest statistics."""
        self.total_return = self.final_balance - self.initial_balance
        self.total_return_pct = (self.total_return / self.initial_balance) * 100

        if len(self.trades) == 0:
            self.total_trades = 0
            self.winning_trades = 0
            self.losing_trades = 0
            self.win_rate = 0.0
            self.avg_win = 0.0
            self.avg_loss = 0.0
            self.profit_factor = 0.0
            self.max_drawdown = 0.0
            self.sharpe_ratio = 0.0
            return

        self.total_trades = len(self.trades)

        # Separate winning and losing trades
        winning = [t for t in self.trades if t.pnl > 0]
        losing = [t for t in self.trades if t.pnl <= 0]

        self.winning_trades = len(winning)
        self.losing_trades = len(losing)
        self.win_rate = (self.winning_trades / self.total_trades) * 100 if self.total_trades > 0 else 0.0

        # Average win/loss
        self.avg_win = sum(t.pnl for t in winning) / len(winning) if winning else 0.0
        self.avg_loss = sum(t.pnl for t in losing) / len(losing) if losing else 0.0

        # Profit factor
        total_profit = sum(t.pnl for t in winning)
        total_loss = abs(sum(t.pnl for t in losing))
        self.profit_factor = total_profit / total_loss if total_loss > 0 else 0.0

        # Max drawdown
        if not self.equity_curve.empty:
            equity = self.equity_curve['equity']
            running_max = equity.expanding().max()
            drawdown = (equity - running_max) / running_max * 100
            self.max_drawdown = drawdown.min()

            # Sharpe ratio (simplified - assuming daily returns)
            returns = equity.pct_change().dropna()
            if len(returns) > 0 and returns.std() > 0:
                self.sharpe_ratio = (returns.mean() / returns.std()) * (252 ** 0.5)  # Annualized
            else:
                self.sharpe_ratio = 0.0
        else:
            self.max_drawdown = 0.0
            self.sharpe_ratio = 0.0

    def print_summary(self):
        """Print backtest summary."""
        print("\n" + "="*60)
        print(f"BACKTEST RESULTS: {self.strategy_name}")
        print("="*60)
        print(f"Period: {self.start_date} to {self.end_date}")
        print(f"\nAccount:")
        print(f"  Initial Balance: ${self.initial_balance:,.2f}")
        print(f"  Final Balance:   ${self.final_balance:,.2f}")
        print(f"  Total Return:    ${self.total_return:,.2f} ({self.total_return_pct:.2f}%)")
        print(f"\nTrades:")
        print(f"  Total Trades:    {self.total_trades}")
        print(f"  Winning Trades:  {self.winning_trades}")
        print(f"  Losing Trades:   {self.losing_trades}")
        print(f"  Win Rate:        {self.win_rate:.2f}%")
        print(f"\nPerformance:")
        print(f"  Avg Win:         ${self.avg_win:.2f}")
        print(f"  Avg Loss:        ${self.avg_loss:.2f}")
        print(f"  Profit Factor:   {self.profit_factor:.2f}")
        print(f"  Max Drawdown:    {self.max_drawdown:.2f}%")
        print(f"  Sharpe Ratio:    {self.sharpe_ratio:.2f}")
        print("="*60 + "\n")


class Backtester:
    """
    Backtesting engine for strategy testing.

    Features:
    - Runs strategy on historical data
    - Simulates order execution with paper broker
    - Tracks equity curve
    - Calculates performance metrics
    """

    def __init__(
        self,
        strategy: BaseStrategy,
        position_sizer: PositionSizer,
        stop_loss_manager: StopLossManager,
        circuit_breaker: CircuitBreaker,
        initial_balance: float = 10000.0
    ):
        self.strategy = strategy
        self.position_sizer = position_sizer
        self.stop_loss_manager = stop_loss_manager
        self.circuit_breaker = circuit_breaker
        self.initial_balance = initial_balance

        logger.info(f"Backtester initialized with strategy '{strategy.name}'")

    async def run(
        self,
        data: pd.DataFrame,
        symbol: str = "BTCUSD",
        lookback_period: int = 50
    ) -> BacktestResult:
        """
        Run backtest on historical data.

        Args:
            data: DataFrame with OHLCV data (must have columns: timestamp, open, high, low, close, volume)
            symbol: Trading symbol
            lookback_period: Minimum data points needed before trading

        Returns:
            BacktestResult object
        """
        logger.info(f"Starting backtest on {len(data)} candles")

        # Initialize broker
        broker = PaperBroker(initial_balance=self.initial_balance)
        await broker.connect()

        # Track equity over time
        equity_curve = []

        # Start from lookback_period to have enough data for indicators
        for i in range(lookback_period, len(data)):
            # Get historical data up to current point
            historical_data = data.iloc[:i+1].copy()
            current_candle = data.iloc[i]

            current_price = current_candle['close']
            timestamp = current_candle['timestamp']

            # Update broker price
            await broker.update_price(symbol, current_price)

            # Check if we should exit any positions
            open_positions = self.strategy.get_open_positions(symbol)
            for position in open_positions:
                should_exit = self.strategy.should_exit(position, current_price, historical_data)

                if should_exit:
                    # Close position
                    broker_side = OrderSide.SELL if position.side == StrategyOrderSide.BUY else OrderSide.BUY

                    order = await broker.place_order(
                        symbol=symbol,
                        side=broker_side,
                        order_type=OrderType.MARKET,
                        quantity=position.size
                    )

                    if order.is_filled():
                        pnl = position.calculate_pnl(order.average_fill_price)
                        self.strategy.close_position(position, order.average_fill_price)
                        self.circuit_breaker.record_trade(pnl)

            # Generate new signal
            signal = self.strategy.analyze(historical_data)

            if signal:
                # Check circuit breaker
                account_balance = await broker.get_account_balance()
                open_count = len(self.strategy.get_open_positions())

                can_trade = self.circuit_breaker.check(account_balance, open_count, [])

                if can_trade:
                    # Check strategy entry conditions
                    should_enter = self.strategy.should_enter(signal, current_price, account_balance)

                    if should_enter:
                        # Calculate position size
                        is_long = signal.side == StrategyOrderSide.BUY
                        stop_loss, take_profit = self.stop_loss_manager.calculate_both(
                            current_price, is_long
                        )

                        quantity = self.position_sizer.calculate_quantity(
                            account_balance,
                            current_price,
                            stop_loss,
                            signal.strength
                        )

                        position_value = quantity * current_price
                        is_valid = self.position_sizer.validate_size(position_value, account_balance)

                        if is_valid:
                            # Place order
                            broker_side = OrderSide.BUY if is_long else OrderSide.SELL

                            order = await broker.place_order(
                                symbol=symbol,
                                side=broker_side,
                                order_type=OrderType.MARKET,
                                quantity=quantity
                            )

                            if order.is_filled():
                                # Create strategy position
                                strategy_position = Position(
                                    symbol=symbol,
                                    side=signal.side,
                                    size=quantity,
                                    entry_price=order.average_fill_price,
                                    stop_loss=stop_loss,
                                    take_profit=take_profit
                                )
                                self.strategy.add_position(strategy_position)

            # Record equity
            portfolio_value = broker.get_portfolio_value()
            equity_curve.append({
                'timestamp': timestamp,
                'equity': portfolio_value,
                'cash': await broker.get_account_balance(),
                'position_value': portfolio_value - await broker.get_account_balance()
            })

        # Close all remaining positions at end
        for position in self.strategy.get_open_positions():
            current_price = await broker.get_current_price(position.symbol)
            if current_price > 0:
                broker_side = OrderSide.SELL if position.side == StrategyOrderSide.BUY else OrderSide.BUY
                order = await broker.place_order(
                    symbol=position.symbol,
                    side=broker_side,
                    order_type=OrderType.MARKET,
                    quantity=position.size
                )
                if order.is_filled():
                    pnl = position.calculate_pnl(order.average_fill_price)
                    self.strategy.close_position(position, order.average_fill_price)

        # Create result
        final_balance = await broker.get_account_balance()
        trades = broker.get_all_trades()
        equity_df = pd.DataFrame(equity_curve)

        result = BacktestResult(
            initial_balance=self.initial_balance,
            final_balance=final_balance,
            trades=trades,
            equity_curve=equity_df,
            strategy_name=self.strategy.name,
            start_date=data.iloc[0]['timestamp'],
            end_date=data.iloc[-1]['timestamp']
        )

        await broker.disconnect()

        logger.info(f"Backtest complete: {result.total_trades} trades, return: {result.total_return_pct:.2f}%")

        return result


# Example usage
async def main():
    from strategy.signal_strategy import TechnicalSignalStrategy
    from risk.position_sizer import PositionSizer, SizingMethod
    from risk.stop_loss import StopLossManager, StopLossType
    from risk.circuit_breaker import CircuitBreaker
    import numpy as np

    # Create sample data
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=200, freq='1h')
    prices = 50000 + np.cumsum(np.random.randn(200) * 100)

    data = pd.DataFrame({
        'timestamp': dates,
        'open': prices + np.random.randn(200) * 50,
        'high': prices + np.abs(np.random.randn(200) * 100),
        'low': prices - np.abs(np.random.randn(200) * 100),
        'close': prices,
        'volume': np.random.randint(1000, 10000, 200)
    })

    # Initialize components
    strategy = TechnicalSignalStrategy()
    position_sizer = PositionSizer(method=SizingMethod.RISK_BASED, risk_per_trade=0.02)
    stop_loss_manager = StopLossManager(stop_loss_type=StopLossType.FIXED_PERCENT)
    circuit_breaker = CircuitBreaker()

    # Run backtest
    backtester = Backtester(
        strategy=strategy,
        position_sizer=position_sizer,
        stop_loss_manager=stop_loss_manager,
        circuit_breaker=circuit_breaker,
        initial_balance=10000.0
    )

    result = await backtester.run(data, symbol="BTCUSD", lookback_period=50)
    result.print_summary()

    # Plot equity curve
    if not result.equity_curve.empty:
        print("\nEquity Curve (last 10 points):")
        print(result.equity_curve.tail(10))


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
