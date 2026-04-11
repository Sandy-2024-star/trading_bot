# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a multi-market automated trading system designed to trade across:
- Cryptocurrency (via Crypto.com MCP)
- Forex (OANDA or FXCM API)
- Indian markets (Zerodha Kite API / NSE / BSE)
- Commodities (MCX)
- With sentiment analysis from global news APIs

## Architecture (5-Layer System)

1. **Data Ingestion Layer** — market feeds + news APIs
2. **Analysis Engine** — technical indicators, fundamental analysis, sentiment analysis, cross-market correlation
3. **Strategy Layer** — signal generation (buy/sell), hedging logic, arbitrage detection
4. **Risk Management** — position sizing, stop-loss automation, circuit breakers
5. **Execution Layer** — broker API connectors, order lifecycle management, backtesting infrastructure
6. **Monitoring** — PnL dashboard, alerting system, Telegram notifications

## Development Phases

- **Phase 1**: ✅ Data ingestion + signal engine
- **Phase 2**: ✅ Strategy + risk engine
- **Phase 3**: ✅ Broker execution + backtesting framework
- **Phase 4**: ✅ Monitoring + live trading

**Current Status**: ALL PHASES COMPLETE! System ready for production deployment.

## Project Structure

```
trading_bot/
├── data/          # ✅ Market data fetchers
│   └── crypto_feed.py        # Crypto.com API integration
├── signals/       # ✅ Technical analysis modules
│   └── technical.py          # RSI, MACD, Bollinger Bands
├── strategy/      # ✅ Trading strategy implementations
│   ├── base_strategy.py      # Abstract strategy base class
│   └── signal_strategy.py    # Technical signal strategies
├── risk/          # ✅ Risk management system
│   ├── position_sizer.py     # Position sizing (fixed, percent, risk-based)
│   ├── stop_loss.py          # Stop loss/take profit calculator
│   └── circuit_breaker.py    # Automatic risk controls
├── execution/     # ✅ Broker execution + backtesting
│   ├── base_broker.py        # Abstract broker interface
│   ├── paper_broker.py       # Paper trading simulator
│   ├── order_manager.py      # Order lifecycle coordinator
│   ├── backtester.py         # Backtesting engine
│   └── performance.py        # Performance metrics analyzer
├── monitoring/    # ✅ Monitoring + live trading
│   ├── pnl_tracker.py        # Real-time PnL tracking
│   ├── alerts.py             # Alert system with handlers
│   ├── telegram_notifier.py  # Telegram integration
│   ├── dashboard_data.py     # Dashboard data aggregator
│   └── live_trader.py        # Live trading coordinator
└── config/        # ✅ Configuration management
    ├── config.py             # Environment-based config loader
    └── settings.example.env  # API key templates
```

## Technology Stack

- **Language**: Python (primary)
- **Data Storage**: Redis (live data caching), PostgreSQL or SQLite (trade history)
- **API Framework**: FastAPI (internal API / dashboard backend)

## Key External References

The project takes inspiration from:
- `freqtrade/freqtrade` — crypto trading bot architecture
- `jesse-ai/jesse` — clean Python algo framework
- `ranaroussi/yfinance` — free historical data
- `backtrader/backtrader` — backtesting framework
- `quantconnect/lean` — enterprise multi-asset engine
- `zerodha/kiteconnect-py` — Indian market broker API

## Working with Context

Always read `Context.md` at the start of each session for current phase goals and status updates.

## Data Sources

- Crypto.com MCP provides: tickers, orderbook, candlestick data
- Forex API (to be configured): OANDA or FXCM
- Indian markets: Zerodha Kite API
- News sentiment: NewsAPI / Alpha Vantage

## Phase 2 Implementation Details

### Strategy Layer (trading_bot/strategy/)
- **BaseStrategy** (base_strategy.py:29): Abstract base class with position tracking, signal analysis, and entry/exit logic
- **TechnicalSignalStrategy** (signal_strategy.py:19): Multi-indicator strategy with configurable thresholds
- **MACDCrossoverStrategy** (signal_strategy.py:202): Simple MACD crossover implementation
- All strategies track open/closed positions and calculate statistics (win rate, PnL)

### Risk Management (trading_bot/risk/)
- **PositionSizer** (position_sizer.py:21): Supports 5 methods (fixed, percent equity, risk-based, Kelly, volatility)
  - Risk-based sizing is recommended: calculates position size from account risk and stop loss distance
- **StopLossManager** (stop_loss.py:18): Calculates stop loss/take profit levels
  - Methods: fixed percent, ATR-based, support/resistance, trailing stops
  - Validates risk/reward ratios before position entry
- **CircuitBreaker** (circuit_breaker.py:17): Automatic trading halts when limits breached
  - Tracks: daily loss %, consecutive losses, drawdown %, position count, daily trade count
  - Cooldown period after trip, auto-reset on new trading day

## Phase 3 Implementation Details

### Execution Layer (trading_bot/execution/)
- **BaseBroker** (base_broker.py:96): Abstract interface for all broker implementations
  - Defines order placement, cancellation, position tracking
  - Account balance management
  - Order and trade history

- **PaperBroker** (paper_broker.py:20): Paper trading simulator for testing without real money
  - Instant market order execution
  - Limit/stop order simulation with price triggers
  - Configurable fees (default 0.1%) and slippage (default 0.05%)
  - Portfolio value calculation (cash + positions)
  - Simulates realistic order fills with slippage

- **OrderManager** (order_manager.py:18): Coordinates strategy signals with broker execution
  - Converts strategy signals to broker orders
  - Applies risk checks before execution (circuit breaker, position sizing)
  - Monitors open positions for exit conditions
  - Syncs strategy positions with broker positions

- **Backtester** (backtester.py:74): Historical strategy testing engine
  - Runs strategies on historical OHLCV data
  - Simulates order execution at historical prices
  - Tracks equity curve over time
  - Handles position entry/exit based on strategy logic
  - Respects circuit breaker rules during backtest

- **PerformanceAnalyzer** (performance.py:14): Comprehensive performance metrics
  - Returns: total return, annualized return, CAGR
  - Trade stats: win rate, profit factor, expectancy, avg win/loss
  - Risk metrics: volatility, downside deviation, VaR, CVaR
  - Drawdown: max drawdown, duration, recovery factor
  - Risk-adjusted ratios: Sharpe, Sortino, Calmar
  - Monthly returns breakdown

## Phase 4 Implementation Details

### Monitoring Layer (trading_bot/monitoring/)
- **PnLTracker** (pnl_tracker.py:22): Real-time profit/loss tracking
  - Records PnL snapshots with timestamp
  - Calculates realized vs unrealized PnL
  - Daily/weekly/monthly aggregation
  - Equity curve generation
  - Automatic daily reset at midnight

- **AlertManager** (alerts.py:37): Comprehensive alert system
  - 4 alert levels: INFO, WARNING, ERROR, CRITICAL
  - 12+ alert types (trade executed, stop loss hit, circuit breaker, etc.)
  - Pluggable handler architecture (console, file, Telegram)
  - Alert history with filtering
  - Configurable thresholds (large profit/loss, low balance, high drawdown)

- **TelegramNotifier** (telegram_notifier.py:16): Telegram bot integration
  - Async message sending via Telegram API
  - Markdown formatting support
  - Daily trading summaries
  - Position updates with live PnL
  - System status notifications
  - Alert filtering by minimum level

- **DashboardData** (dashboard_data.py:17): Data aggregation for monitoring
  - Account overview (balance, equity, returns, daily PnL)
  - Open positions with unrealized PnL and duration
  - Recent trades history
  - Performance metrics (win rate, profit factor)
  - Risk status (circuit breaker state, trading allowed)
  - Recent alerts feed
  - System health (uptime, open positions/orders)
  - Console dashboard printer with real-time updates

- **LiveTrader** (live_trader.py:25): Live trading coordinator
  - Automated trading loop with configurable interval
  - Integrates all system components (feed, broker, strategy, risk, monitoring)
  - Real-time PnL tracking after each iteration
  - Dashboard updates every cycle
  - Alert notifications for all trading events
  - Graceful start/stop with position cleanup
  - Optional Telegram integration
  - Runs indefinitely until stopped

## Running the System

```bash
# Phase 1 demo: Data ingestion and signal generation
python main.py

# Phase 2 demo: Full strategy execution with risk management
python main.py phase2

# Phase 3 demo: Backtesting on historical data
python main.py phase3

# Phase 4 demo: Live trading with monitoring (90 second demo)
python main.py phase4
```

## Key Development Considerations

### General
- When building signal generators, implement common technical indicators: RSI, MACD, Bollinger Bands, moving averages
- All broker API keys should be stored in `config/` directory (gitignored)
- Cross-market correlation analysis is essential for identifying arbitrage opportunities

### Risk Management
- Risk management should be fail-safe: circuit breakers trigger before position limits are exceeded
- Position sizing uses risk-based method by default (2% risk per trade)
- Stop loss levels are mandatory for risk-based position sizing
- Circuit breaker automatically halts trading after 3 consecutive losses or 5% daily loss

### Backtesting & Execution
- Backtesting uses the same signal/strategy logic as live execution
- Paper broker simulates realistic slippage (0.05%) and fees (0.1%)
- All orders go through OrderManager which applies risk checks
- Backtest results include comprehensive performance metrics (Sharpe, Sortino, Calmar ratios)
- Equity curve is tracked throughout backtest for drawdown analysis
- Minimum 50 candles (lookback period) required before strategy starts trading in backtest

### Performance Metrics
- Sharpe ratio measures risk-adjusted returns (returns / volatility)
- Sortino ratio uses downside deviation instead of total volatility
- Calmar ratio is annualized return divided by max drawdown
- Profit factor is total profit / total loss (>1 is profitable)
- Expectancy is average expected profit per trade
