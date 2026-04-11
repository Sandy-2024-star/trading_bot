"""
Strategy Parameter Tuning Script.
Runs multiple backtests with different parameter combinations to find the optimal setup for a specific symbol.
"""

import asyncio
import itertools
import sys
import os
import pandas as pd
from typing import Dict, List, Any
from datetime import datetime
from loguru import logger

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.factory import create_market_data_feed
from strategy.signal_strategy import TechnicalSignalStrategy
from risk.position_sizer import PositionSizer, SizingMethod
from risk.stop_loss import StopLossManager, StopLossType
from risk.circuit_breaker import CircuitBreaker
from execution.backtester import Backtester
from ai.lstm_model import LSTMPricePredictor

async def tune_symbol(symbol: str, timeframe: str = "1h", limit: int = 500):
    """
    Find best parameters for a specific symbol.
    """
    logger.info(f"Tuning parameters for {symbol} on {timeframe} timeframe...")
    
    # 1. Fetch historical data
    feed = create_market_data_feed()
    data = await feed.get_candlesticks(symbol, timeframe=timeframe, limit=limit)
    await feed.close()
    
    if data.empty:
        logger.error(f"No data available for {symbol}")
        return

    # 1a. Train LSTM Model
    predictor = LSTMPricePredictor(symbol)
    await predictor.train(data, epochs=15)

    # 2. Define parameter search space
    # Example: RSI periods, MACD settings, etc.
    param_grid = {
        "rsi_period": [10, 14, 20],
        "rsi_oversold": [25, 30, 35],
        "rsi_overbought": [65, 70, 75],
        "sma_fast": [10, 20],
        "sma_slow": [50, 100],
    }
    
    # Generate all combinations
    keys, values = zip(*param_grid.items())
    combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]
    
    logger.info(f"Testing {len(combinations)} combinations...")
    
    results = []
    
    # 3. Iterate and backtest
    for i, params in enumerate(combinations):
        if i % 10 == 0:
            logger.info(f"Progress: {i}/{len(combinations)}")
            
        # Initialize strategy with current params
        strategy = TechnicalSignalStrategy(
            name=f"Tune_{i}",
            symbol_params={symbol: params},
            signal_threshold=0.4
        )
        
        # Risk components
        position_sizer = PositionSizer(method=SizingMethod.PERCENT_EQUITY, risk_per_trade=0.02)
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
        
        try:
            result = await backtester.run(data, symbol=symbol, lookback_period=100)
            
            results.append({
                "params": params,
                "return_pct": result.total_return_pct,
                "trades": result.total_trades,
                "win_rate": result.win_rate,
                "sharpe": result.sharpe_ratio,
                "drawdown": result.max_drawdown
            })
        except Exception as e:
            logger.error(f"Error in backtest {i}: {e}")

    # 4. Analyze results
    if not results:
        logger.error("No successful backtests completed")
        return

    df_results = pd.DataFrame(results)
    
    # Sort by Sharpe Ratio (best risk-adjusted return)
    best = df_results.sort_values("sharpe", ascending=False).iloc[0]
    
    print("\n" + "="*60)
    print(f"TUNING RESULTS FOR {symbol}")
    print("="*60)
    print(f"Best Sharpe Ratio: {best['sharpe']:.2f}")
    print(f"Best Return:       {best['return_pct']:.2f}%")
    print(f"Total Trades:      {best['trades']}")
    print(f"Win Rate:          {best['win_rate']:.1f}%")
    print(f"Max Drawdown:      {best['drawdown']:.2f}%")
    print("\nOptimal Parameters:")
    for k, v in best['params'].items():
        print(f"  {k}: {v}")
    print("="*60 + "\n")
    
    # 5. Save best params to a JSON file
    import json
    config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")
    tuning_file = os.path.join(config_dir, "symbol_params.json")
    
    all_params = {}
    if os.path.exists(tuning_file):
        try:
            with open(tuning_file, 'r') as f:
                all_params = json.load(f)
        except:
            pass
            
    all_params[symbol] = best['params']
    
    with open(tuning_file, 'w') as f:
        json.dump(all_params, f, indent=4)
        
    logger.info(f"Best parameters for {symbol} saved to {tuning_file}")

if __name__ == "__main__":
    symbol = "BTCUSD"
    if len(sys.argv) > 1:
        symbol = sys.argv[1]
        
    asyncio.run(tune_symbol(symbol))
