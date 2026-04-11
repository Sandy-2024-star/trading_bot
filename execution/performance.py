"""
Performance analysis and metrics calculation.
"""

import pandas as pd
import numpy as np
from typing import List, Dict
from datetime import datetime
from loguru import logger

from core.base_broker import Trade


class PerformanceAnalyzer:
    """
    Analyzes trading performance and calculates various metrics.

    Metrics:
    - Returns (total, annualized)
    - Win rate, profit factor
    - Sharpe ratio, Sortino ratio
    - Maximum drawdown
    - Risk-adjusted returns
    - Trade statistics
    """

    def __init__(self, trades: List[Trade], equity_curve: pd.DataFrame, initial_balance: float):
        self.trades = trades
        self.equity_curve = equity_curve
        self.initial_balance = initial_balance

        logger.info(f"PerformanceAnalyzer initialized with {len(trades)} trades")

    def calculate_all_metrics(self) -> Dict:
        """Calculate all performance metrics."""
        return {
            **self.calculate_returns(),
            **self.calculate_trade_statistics(),
            **self.calculate_risk_metrics(),
            **self.calculate_drawdown_metrics(),
            **self.calculate_ratios()
        }

    def calculate_returns(self) -> Dict:
        """Calculate return metrics."""
        if self.equity_curve.empty:
            return {
                "total_return": 0.0,
                "total_return_pct": 0.0,
                "annualized_return": 0.0,
                "cagr": 0.0
            }

        final_equity = self.equity_curve['equity'].iloc[-1]
        total_return = final_equity - self.initial_balance
        total_return_pct = (total_return / self.initial_balance) * 100

        # Calculate annualized return
        days = (self.equity_curve['timestamp'].iloc[-1] - self.equity_curve['timestamp'].iloc[0]).days
        years = days / 365.25 if days > 0 else 1

        cagr = ((final_equity / self.initial_balance) ** (1 / years) - 1) * 100 if years > 0 else 0.0
        annualized_return = (total_return / self.initial_balance / years) * 100 if years > 0 else 0.0

        return {
            "total_return": total_return,
            "total_return_pct": total_return_pct,
            "annualized_return": annualized_return,
            "cagr": cagr
        }

    def calculate_trade_statistics(self) -> Dict:
        """Calculate trade-related statistics."""
        if not self.trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "largest_win": 0.0,
                "largest_loss": 0.0,
                "avg_trade_pnl": 0.0,
                "profit_factor": 0.0,
                "expectancy": 0.0
            }

        total_trades = len(self.trades)
        winning = [t for t in self.trades if t.pnl > 0]
        losing = [t for t in self.trades if t.pnl <= 0]

        winning_trades = len(winning)
        losing_trades = len(losing)
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0.0

        avg_win = sum(t.pnl for t in winning) / len(winning) if winning else 0.0
        avg_loss = sum(t.pnl for t in losing) / len(losing) if losing else 0.0

        largest_win = max((t.pnl for t in winning), default=0.0)
        largest_loss = min((t.pnl for t in losing), default=0.0)

        avg_trade_pnl = sum(t.pnl for t in self.trades) / total_trades

        # Profit factor
        total_profit = sum(t.pnl for t in winning)
        total_loss = abs(sum(t.pnl for t in losing))
        profit_factor = total_profit / total_loss if total_loss > 0 else 0.0

        # Expectancy
        win_prob = win_rate / 100
        loss_prob = 1 - win_prob
        expectancy = (win_prob * avg_win) - (loss_prob * abs(avg_loss))

        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "largest_win": largest_win,
            "largest_loss": largest_loss,
            "avg_trade_pnl": avg_trade_pnl,
            "profit_factor": profit_factor,
            "expectancy": expectancy
        }

    def calculate_risk_metrics(self) -> Dict:
        """Calculate risk-related metrics."""
        if self.equity_curve.empty:
            return {
                "volatility": 0.0,
                "downside_deviation": 0.0,
                "var_95": 0.0,
                "cvar_95": 0.0
            }

        returns = self.equity_curve['equity'].pct_change().dropna()

        if len(returns) == 0:
            return {
                "volatility": 0.0,
                "downside_deviation": 0.0,
                "var_95": 0.0,
                "cvar_95": 0.0
            }

        # Volatility (annualized)
        volatility = returns.std() * np.sqrt(252) * 100  # Assuming daily-ish data

        # Downside deviation (for Sortino ratio)
        negative_returns = returns[returns < 0]
        downside_deviation = negative_returns.std() * np.sqrt(252) * 100 if len(negative_returns) > 0 else 0.0

        # Value at Risk (95% confidence)
        var_95 = np.percentile(returns, 5) * 100

        # Conditional Value at Risk (CVaR/Expected Shortfall)
        cvar_95 = returns[returns <= np.percentile(returns, 5)].mean() * 100 if len(returns) > 0 else 0.0

        return {
            "volatility": volatility,
            "downside_deviation": downside_deviation,
            "var_95": var_95,
            "cvar_95": cvar_95
        }

    def calculate_drawdown_metrics(self) -> Dict:
        """Calculate drawdown-related metrics."""
        if self.equity_curve.empty:
            return {
                "max_drawdown": 0.0,
                "max_drawdown_duration": 0,
                "avg_drawdown": 0.0,
                "recovery_factor": 0.0
            }

        equity = self.equity_curve['equity']
        running_max = equity.expanding().max()
        drawdown = (equity - running_max) / running_max * 100

        max_drawdown = drawdown.min()

        # Drawdown duration
        in_drawdown = drawdown < 0
        drawdown_periods = []
        current_period = 0

        for is_dd in in_drawdown:
            if is_dd:
                current_period += 1
            else:
                if current_period > 0:
                    drawdown_periods.append(current_period)
                current_period = 0

        max_drawdown_duration = max(drawdown_periods, default=0)
        avg_drawdown = drawdown[drawdown < 0].mean() if (drawdown < 0).any() else 0.0

        # Recovery factor
        total_return = equity.iloc[-1] - self.initial_balance
        recovery_factor = total_return / abs(max_drawdown) if max_drawdown != 0 else 0.0

        return {
            "max_drawdown": max_drawdown,
            "max_drawdown_duration": max_drawdown_duration,
            "avg_drawdown": avg_drawdown,
            "recovery_factor": recovery_factor
        }

    def calculate_ratios(self) -> Dict:
        """Calculate risk-adjusted return ratios."""
        if self.equity_curve.empty:
            return {
                "sharpe_ratio": 0.0,
                "sortino_ratio": 0.0,
                "calmar_ratio": 0.0
            }

        returns = self.equity_curve['equity'].pct_change().dropna()

        if len(returns) == 0 or returns.std() == 0:
            return {
                "sharpe_ratio": 0.0,
                "sortino_ratio": 0.0,
                "calmar_ratio": 0.0
            }

        # Sharpe Ratio (annualized, risk-free rate = 0)
        sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252)

        # Sortino Ratio (annualized)
        negative_returns = returns[returns < 0]
        downside_std = negative_returns.std() if len(negative_returns) > 0 else 0.0
        sortino_ratio = (returns.mean() / downside_std) * np.sqrt(252) if downside_std > 0 else 0.0

        # Calmar Ratio (annualized return / max drawdown)
        returns_metrics = self.calculate_returns()
        drawdown_metrics = self.calculate_drawdown_metrics()

        calmar_ratio = (
            returns_metrics['annualized_return'] / abs(drawdown_metrics['max_drawdown'])
            if drawdown_metrics['max_drawdown'] != 0 else 0.0
        )

        return {
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "calmar_ratio": calmar_ratio
        }

    def print_report(self):
        """Print comprehensive performance report."""
        metrics = self.calculate_all_metrics()

        print("\n" + "="*70)
        print("PERFORMANCE REPORT")
        print("="*70)

        print("\n📈 RETURNS")
        print(f"  Total Return:        ${metrics['total_return']:>12,.2f}  ({metrics['total_return_pct']:>6.2f}%)")
        print(f"  Annualized Return:                               {metrics['annualized_return']:>6.2f}%")
        print(f"  CAGR:                                            {metrics['cagr']:>6.2f}%")

        print("\n📊 TRADE STATISTICS")
        print(f"  Total Trades:        {metrics['total_trades']:>12,}")
        print(f"  Winning Trades:      {metrics['winning_trades']:>12,}")
        print(f"  Losing Trades:       {metrics['losing_trades']:>12,}")
        print(f"  Win Rate:                                        {metrics['win_rate']:>6.2f}%")
        print(f"  Avg Win:             ${metrics['avg_win']:>12,.2f}")
        print(f"  Avg Loss:            ${metrics['avg_loss']:>12,.2f}")
        print(f"  Largest Win:         ${metrics['largest_win']:>12,.2f}")
        print(f"  Largest Loss:        ${metrics['largest_loss']:>12,.2f}")
        print(f"  Profit Factor:       {metrics['profit_factor']:>13.2f}")
        print(f"  Expectancy:          ${metrics['expectancy']:>12,.2f}")

        print("\n⚠️  RISK METRICS")
        print(f"  Volatility:                                      {metrics['volatility']:>6.2f}%")
        print(f"  Downside Deviation:                              {metrics['downside_deviation']:>6.2f}%")
        print(f"  Value at Risk (95%):                             {metrics['var_95']:>6.2f}%")
        print(f"  CVaR (95%):                                      {metrics['cvar_95']:>6.2f}%")

        print("\n📉 DRAWDOWN")
        print(f"  Max Drawdown:                                    {metrics['max_drawdown']:>6.2f}%")
        print(f"  Max DD Duration:     {metrics['max_drawdown_duration']:>12,} periods")
        print(f"  Avg Drawdown:                                    {metrics['avg_drawdown']:>6.2f}%")
        print(f"  Recovery Factor:     {metrics['recovery_factor']:>13.2f}")

        print("\n🎯 RISK-ADJUSTED RATIOS")
        print(f"  Sharpe Ratio:        {metrics['sharpe_ratio']:>13.2f}")
        print(f"  Sortino Ratio:       {metrics['sortino_ratio']:>13.2f}")
        print(f"  Calmar Ratio:        {metrics['calmar_ratio']:>13.2f}")

        print("="*70 + "\n")

    def get_monthly_returns(self) -> pd.DataFrame:
        """Calculate monthly returns."""
        if self.equity_curve.empty:
            return pd.DataFrame()

        df = self.equity_curve.copy()
        df['year_month'] = pd.to_datetime(df['timestamp']).dt.to_period('M')

        monthly = df.groupby('year_month').agg({
            'equity': ['first', 'last']
        })

        monthly.columns = ['start_equity', 'end_equity']
        monthly['return'] = (monthly['end_equity'] - monthly['start_equity']) / monthly['start_equity'] * 100

        return monthly


# Example usage
def main():
    from core.base_broker import Trade, OrderSide
    import numpy as np

    # Create sample trades
    np.random.seed(42)
    trades = []

    for i in range(50):
        pnl = np.random.randn() * 100  # Random PnL
        trade = Trade(
            trade_id=f"t{i}",
            order_id=f"o{i}",
            symbol="BTCUSD",
            side=OrderSide.BUY,
            quantity=0.1,
            price=50000 + np.random.randn() * 1000,
            fees=10.0,
            timestamp=datetime.now(),
            pnl=pnl
        )
        trades.append(trade)

    # Create sample equity curve
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    equity = 10000 + np.cumsum(np.random.randn(100) * 100)

    equity_curve = pd.DataFrame({
        'timestamp': dates,
        'equity': equity,
        'cash': equity * 0.8,
        'position_value': equity * 0.2
    })

    # Analyze performance
    analyzer = PerformanceAnalyzer(trades, equity_curve, 10000.0)
    analyzer.print_report()

    # Get monthly returns
    monthly = analyzer.get_monthly_returns()
    if not monthly.empty:
        print("Monthly Returns:")
        print(monthly)


if __name__ == "__main__":
    main()
