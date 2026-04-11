# AI Assistant Context - Trading Bot Project

**Document Purpose**: Enable any AI assistant (Claude, GPT-4, Gemini, Codex, etc.) to understand this project completely and resume work seamlessly.

**Last Updated**: 2026-03-31 (Updated: Phase 5 Progress)
**Project Version**: 1.5.0
**Current Phase**: Phase 5 In Progress - Sentiment Analysis & Multi-Source Data

---

## 🆕 What's New (March 31, 2026 Update)

**Major Update**: Phase 5 features implemented - Sentiment-aware trading is now live!

### New Capabilities
1. ✅ **Multi-Source Data** - CoinGecko (crypto), Alpha Vantage (forex + news), NewsAPI
2. ✅ **Sentiment Analysis** - Keyword-based scoring, article aggregation
3. ✅ **Sentiment-Aware Trading** - Signals adjusted by sentiment, entry filtering
4. ✅ **Market Context** - News, sentiment, forex rates available to strategies
5. ✅ **Provider Switching** - Factory pattern, config-based selection

### Files Added (5 new)
- `data/coingecko_feed.py` - Free crypto data (now default)
- `data/alpha_vantage_feed.py` - Forex + news sentiment
- `data/newsapi_feed.py` - Market news search
- `data/factory.py` - Provider factory
- `signals/sentiment.py` - Sentiment analyzer

### Files Enhanced (8 modified)
- `strategy/base_strategy.py` - Market context support
- `strategy/signal_strategy.py` - Sentiment integration
- `monitoring/live_trader.py` - Context refresh loop
- `config/config.py` - Multi-provider config
- Plus: order_manager.py, paper_broker.py, dashboard_data.py, web_dashboard.py

### Breaking Changes
- Default provider changed from Crypto.com → CoinGecko
- Strategy signals now include sentiment indicators
- LiveTrader requires news/forex feeds (optional but recommended)

---

## Quick Start for AI Assistants

### First Actions When Resuming Work

1. **Read these files in order**:
   - `Context.md` - Original project goals and architecture
   - `README.md` - Project structure and usage
   - `ROADMAP.md` - Pending tasks and future enhancements
   - This file (`AI_CONTEXT.md`) - Complete project context

2. **Check current status**:
   ```bash
   # View running processes
   ps aux | grep python3

   # Check if web dashboard is running
   curl http://localhost:8000/api/dashboard

   # Check logs
   tail -f /tmp/claude/tasks/*.output
   ```

3. **Understand the user's likely intent**:
   - If they say "continue" or "next" → Check ROADMAP.md for next priority task
   - If they mention errors → Look at recent logs and fix issues
   - If they want new features → Implement based on ROADMAP.md priorities

---

## Project Overview

### What This Project Does

This is a **multi-market automated trading system** designed to:
- Fetch real-time market data from multiple sources
- Analyze data using technical indicators
- Generate trading signals based on strategies
- Manage risk (position sizing, stop-loss, circuit breakers)
- Execute trades via broker APIs (currently paper trading)
- Monitor performance with real-time dashboard
- Send alerts via Telegram/email

### Target Markets
- ✅ Cryptocurrency (Crypto.com API - partially integrated)
- ⏳ Forex (OANDA/FXCM - planned)
- ⏳ Indian Stock Market (Zerodha Kite API - planned)
- ⏳ Commodities (MCX - planned)

### Current State (Updated March 31, 2026)
- **Status**: Phase 5 in progress - Sentiment analysis implemented ✅
- **What works**:
  - ✅ Multi-source data (CoinGecko, Alpha Vantage, NewsAPI)
  - ✅ Sentiment analysis engine
  - ✅ Sentiment-aware trading signals
  - ✅ Market context integration
  - ✅ Forex rate tracking (EUR/USD)
  - ✅ News aggregation
  - ✅ Factory pattern for data providers
  - ✅ Paper trading, risk management, web dashboard
- **What doesn't work**: Real broker integration, database persistence
- **Known issues**: ~~Crypto.com API~~ (Resolved: using CoinGecko now)

---

## Project Architecture

### 5-Layer Architecture

```
┌─────────────────────────────────────────────────┐
│  Layer 5: MONITORING                           │
│  - PnL tracking, alerts, dashboard, Telegram   │
└─────────────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────────────┐
│  Layer 4: EXECUTION                            │
│  - Broker APIs, order management, backtesting  │
└─────────────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────────────┐
│  Layer 3: RISK MANAGEMENT                      │
│  - Position sizing, stop-loss, circuit breaker │
└─────────────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────────────┐
│  Layer 2: STRATEGY                             │
│  - Trading strategies, signal generation       │
└─────────────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────────────┐
│  Layer 1: DATA INGESTION                       │
│  - Market data feeds, technical indicators     │
└─────────────────────────────────────────────────┘
```

### Data Flow

```
Market Data → Technical Analysis → Strategy Signals → Risk Checks
→ Order Execution → Position Tracking → Performance Monitoring
```

---

## Directory Structure & Key Files

### Root Directory
```
/Users/link/TestLab/Other/Market/trading_bot/
├── main.py                    # Main entry point, demo runners
├── requirements.txt           # Python dependencies
├── README.md                  # User documentation
├── Context.md                 # Original project context
├── ROADMAP.md                 # Future enhancements
├── AI_CONTEXT.md             # This file
└── config/
    ├── config.py             # Configuration loader
    ├── settings.example.env  # Example environment file
    └── .env                  # Actual API keys (not created yet)
```

### Module Structure

#### 1. Data Layer (`/data/`) - **Recently Expanded** ⭐

**Purpose**: Fetch market data from external APIs

- **`crypto_feed.py`** (363 lines)
  - Class: `CryptoFeed`
  - API: Crypto.com Exchange API v1
  - Methods: `get_ticker()`, `get_candlesticks()`, `get_orderbook()`
  - **Status**: Available but not default (has 400 errors)

- **`coingecko_feed.py`** ⭐ NEW (201 lines)
  - Class: `CoinGeckoFeed`
  - API: CoinGecko API v3 (FREE, no key required)
  - Symbols: BTC, ETH, SOL, XRP, DOGE, ADA, BNB, AVAX, MATIC
  - Methods:
    - `get_ticker(symbol)` - Current price
    - `get_candlesticks(symbol, timeframe, limit)` - OHLCV data
  - **Status**: ✅ Default provider, working perfectly

- **`alpha_vantage_feed.py`** ⭐ NEW (227 lines)
  - Class: `AlphaVantageFeed`
  - API: Alpha Vantage (FREE, requires API key)
  - Features:
    - Forex exchange rates (EUR/USD, etc.)
    - News sentiment data
    - Rate limiting (12 sec between requests)
  - Methods:
    - `get_exchange_rate(from_to)` - Forex rates
    - `get_news_sentiment(topics, limit)` - Market news with sentiment
  - **Status**: ✅ Working, used for context enrichment

- **`newsapi_feed.py`** ⭐ NEW (77 lines)
  - Class: `NewsAPIFeed`
  - API: NewsAPI.org (FREE, requires API key)
  - Methods:
    - `search_everything(query, from_date, page_size)` - Article search
    - `search_market_news(query, page_size)` - Convenience wrapper
  - **Status**: ✅ Working, used for sentiment analysis

- **`factory.py`** ⭐ NEW (31 lines)
  - Function: `create_market_data_feed(provider)`
  - Factory pattern for data provider selection
  - Config-based provider switching
  - **Status**: ✅ Working

#### 2. Signals Layer (`/signals/`) - **Recently Expanded** ⭐

**Purpose**: Calculate technical indicators and generate signals

- **`technical.py`** (187 lines)
  - Class: `TechnicalIndicators`
  - Indicators:
    - RSI (Relative Strength Index)
    - MACD (Moving Average Convergence Divergence)
    - Bollinger Bands
    - Moving Averages (SMA/EMA)
  - Method: `generate_signals(df)` - Returns signal (-1, 0, 1)
  - Signal Logic:
    - BUY: RSI < 30, MACD cross up, price < lower BB
    - SELL: RSI > 70, MACD cross down, price > upper BB

- **`sentiment.py`** ⭐ NEW (67 lines)
  - Class: `SentimentAnalyzer`
  - Algorithm: Keyword-based sentiment scoring
  - Keywords:
    - Positive: beat, bullish, buy, gain, growth, rally, etc. (13 keywords)
    - Negative: ban, bearish, crash, decline, drop, hack, etc. (14 keywords)
  - Method: `score_articles(articles)` - Returns dict with:
    - `score` (float -1.0 to 1.0)
    - `label` (BULLISH/BEARISH/NEUTRAL)
    - `article_count` (int)
  - Scoring Logic:
    - Score = (positive - negative) / total
    - BULLISH: score >= 0.25
    - BEARISH: score <= -0.25
    - NEUTRAL: -0.25 < score < 0.25
  - **Status**: ✅ Working, integrated into strategy

#### 3. Strategy Layer (`/strategy/`) - **Recently Enhanced** ⭐

**Purpose**: Define trading strategies

- **`base_strategy.py`** (230 lines → Enhanced)
  - Classes: `Position`, `Signal`, `OrderSide`, `BaseStrategy`
  - Abstract methods to implement:
    - `analyze(data)` - Generate signals
    - `should_enter(signal, price, balance)` - Entry logic
    - `should_exit(position, price)` - Exit logic
  - **NEW**: Market context support ⭐
    - `market_context: Dict[str, Dict]` - Store sentiment/macro data per symbol
    - `update_market_context(symbol, context)` - Update context
    - `get_market_context(symbol)` - Retrieve context

- **`signal_strategy.py`** (145 lines → 320 lines, Enhanced) ⭐
  - Class: `TechnicalSignalStrategy`
  - Implements technical indicator-based trading
  - **NEW**: Sentiment-aware signal generation ⭐
    - Retrieves sentiment from market context
    - Adjusts signal strength by 30% based on sentiment
    - Example: Tech signal 0.7 + Sentiment 0.5 × 0.3 = 0.85
  - **NEW**: Entry filtering based on sentiment ⭐
    - Blocks BUY if sentiment <= -0.35 (strong bearish)
    - Blocks SELL if sentiment >= 0.35 (strong bullish)
  - **NEW**: Signal includes sentiment indicators ⭐
    - `sentiment_score`, `sentiment_label`, `article_count`
    - `eurusd_rate`, `news_provider`, `forex_provider`
  - Configurable signal threshold (default: 0.5)
  - Auto stop-loss and take-profit

#### 4. Risk Management Layer (`/risk/`)
**Purpose**: Control trading risk

- **`position_sizer.py`** (158 lines)
  - Class: `PositionSizer`
  - Methods:
    - `FIXED` - Fixed dollar amount
    - `PERCENT_EQUITY` - % of account
    - `RISK_BASED` - Based on stop-loss distance (recommended)
    - `KELLY` - Kelly criterion
    - `VOLATILITY` - ATR-based sizing

- **`stop_loss.py`** (195 lines)
  - Class: `StopLossManager`
  - Types:
    - `FIXED_PERCENT` - Fixed % from entry
    - `ATR` - Based on Average True Range
    - `SUPPORT_RESISTANCE` - Technical levels
    - `TRAILING` - Follows price

- **`circuit_breaker.py`** (180 lines)
  - Class: `CircuitBreaker`
  - Checks:
    - Max daily loss (default: 5%)
    - Max consecutive losses (default: 3)
    - Max drawdown (default: 15%)
    - Position count limits
    - Daily trade limits

#### 5. Execution Layer (`/execution/`)
**Purpose**: Execute trades and backtest strategies

- **`base_broker.py`** (187 lines)
  - Abstract class for broker implementations
  - Order types: Market, Limit, Stop

- **`paper_broker.py`** (267 lines)
  - Class: `PaperBroker`
  - Paper trading simulator
  - Instant market order fills
  - Configurable fees (default: 0.1%) and slippage (0.05%)
  - Starting balance: $10,000

- **`order_manager.py`** (320 lines)
  - Class: `OrderManager`
  - Coordinates strategy ↔ broker
  - Applies risk management
  - Monitors stop-loss and take-profit

- **`backtester.py`** (245 lines)
  - Class: `Backtester`
  - Runs strategies on historical data
  - Bar-by-bar simulation
  - Returns: trades, equity curve, metrics

- **`performance.py`** (389 lines)
  - Class: `PerformanceAnalyzer`
  - Metrics:
    - Returns (total, annual, CAGR)
    - Win rate, profit factor
    - Sharpe, Sortino, Calmar ratios
    - Max drawdown, VaR, CVaR
  - Method: `print_report()` - Full analysis

#### 6. Monitoring Layer (`/monitoring/`)
**Purpose**: Track performance and send alerts

- **`pnl_tracker.py`** (198 lines)
  - Class: `PnLTracker`
  - Real-time PnL snapshots
  - Daily/weekly/monthly aggregation
  - Equity curve generation

- **`alerts.py`** (223 lines)
  - Class: `AlertManager`
  - Enums: `AlertType`, `AlertLevel`
  - Alert types: trade executed, stop-loss hit, system error, etc.
  - Pluggable handlers (console, Telegram, email)

- **`telegram_notifier.py`** (168 lines)
  - Class: `TelegramNotifier`
  - Async Telegram bot integration
  - Methods: `send_message()`, `send_daily_summary()`
  - Requires: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

- **`dashboard_data.py`** (195 lines)
  - Class: `DashboardData`
  - Aggregates data from all components
  - Methods:
    - `get_account_overview()`
    - `get_open_positions()`
    - `get_recent_trades()`
    - `get_performance_metrics()`
    - `get_risk_status()`

- **`live_trader.py`** (299 lines → 450+ lines, Enhanced) ⭐
  - Class: `LiveTrader`
  - Main trading loop coordinator
  - Update interval: 60 seconds (configurable)
  - **NEW**: Context refresh interval: 30 minutes ⭐
  - **NEW**: Multi-source integration ⭐
    - `news_feed: NewsAPIFeed` - Market news
    - `fx_feed: AlphaVantageFeed` - Forex + sentiment
    - `SYMBOL_ALIASES` - Map symbols to news keywords
  - **NEW**: Market context refresh ⭐
    - `_refresh_market_context()` - Update sentiment/forex every 30min
    - `_extract_base_symbol()` - Parse trading pairs (BTCUSD → BTC)
    - `_close_context_feeds()` - Clean shutdown
  - Enhanced Workflow:
    1. **Refresh context** (if 30min elapsed) ⭐ NEW
    2. Fetch market data
    3. Check exits for open positions
    4. Generate new signals (with sentiment) ⭐ ENHANCED
    5. Process signals through order manager
    6. Update PnL tracking
    7. Print dashboard
    8. Sleep and repeat

- **`web_dashboard.py`** (597 lines)
  - Class: `WebDashboard`
  - FastAPI web server
  - Endpoints:
    - `GET /` - HTML dashboard
    - `GET /api/dashboard` - JSON data
    - `WS /ws` - WebSocket for real-time updates (planned)
  - Features:
    - Light/Dark/System theme switching
    - Auto-refresh every 3 seconds
    - Live account overview
    - Position tracking
    - Recent trades list
    - Performance metrics
    - Risk status
  - Current URL: http://localhost:8000

---

## Key Configuration

### Environment Variables (`.env` file)

**Current State**: File doesn't exist yet (should be created from `settings.example.env`)

```env
# Data Providers ⭐ NEW
MARKET_DATA_PROVIDER=coingecko    # Options: coingecko, crypto_com
FOREX_DATA_PROVIDER=alpha_vantage # Options: alpha_vantage, oanda (planned)
NEWS_DATA_PROVIDER=newsapi        # Options: newsapi, alpha_vantage

# Crypto APIs
CRYPTO_COM_API_KEY=your_key_here       # Optional (not default)
CRYPTO_COM_SECRET_KEY=your_secret_here
COINGECKO_API_KEY=                     # Optional (free tier works without key)

# News & Sentiment APIs ⭐ NEW
NEWS_API_KEY=your_key_here             # Get from newsapi.org
ALPHA_VANTAGE_API_KEY=your_key_here    # Get from alphavantage.co

# Forex Broker APIs (Planned)
OANDA_API_KEY=your_key_here
OANDA_ACCOUNT_ID=your_account_id
OANDA_ENVIRONMENT=practice             # Options: practice, live

# Telegram Notifications
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Database
REDIS_HOST=localhost
REDIS_PORT=6379
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=trading_bot
POSTGRES_USER=postgres
POSTGRES_PASSWORD=

# Execution Mode ⭐ NEW
EXECUTION_MODE=paper                   # Options: paper, real
REAL_BROKER_PROVIDER=oanda            # For when EXECUTION_MODE=real

# Risk Limits
MAX_POSITION_SIZE=10000
RISK_PER_TRADE=0.02
STOP_LOSS_PERCENT=0.05

# System
LOG_LEVEL=INFO
ENVIRONMENT=development                # Options: development, production
```

### Command Line Usage

```bash
# Phase 1: Data ingestion + signals
python3 main.py
python3 main.py phase1

# Phase 2: Strategy + risk management
python3 main.py phase2

# Phase 3: Backtesting
python3 main.py phase3

# Phase 4: Live trading (console)
python3 main.py phase4

# Web Dashboard (current)
python3 main.py web
python3 main.py dashboard
```

---

## Common Development Tasks

### Adding a New Strategy

1. Create new file in `/strategy/`
2. Inherit from `BaseStrategy`
3. Implement required methods:
   ```python
   from strategy.base_strategy import BaseStrategy, Signal, OrderSide

   class MyStrategy(BaseStrategy):
       def analyze(self, data):
           # Your logic here
           return Signal(
               symbol="BTCUSD",
               side=OrderSide.BUY,
               strength=0.8,
               reason="My signal logic"
           )

       def should_enter(self, signal, current_price, account_balance):
           return signal.strength > 0.7

       def should_exit(self, position, current_price):
           # Exit logic
           return False
   ```
4. Test with backtester
5. Add to `main.py` demo

### Adding a New Market Data Feed

1. Create new file in `/data/`
2. Implement similar interface to `CryptoFeed`:
   ```python
   class ForexFeed:
       async def get_ticker(self, symbol):
           # Fetch from OANDA API
           pass

       async def get_candlesticks(self, symbol, timeframe, limit):
           # Return pandas DataFrame with OHLCV
           pass
   ```
3. Update `LiveTrader` to support multiple feeds
4. Add configuration to `.env`

### Adding a New Broker

1. Create file in `/execution/`
2. Inherit from `BaseBroker`
3. Implement abstract methods:
   ```python
   from execution.base_broker import BaseBroker, Order, OrderStatus

   class MyBroker(BaseBroker):
       async def place_order(self, order):
           # Call broker API
           pass

       async def cancel_order(self, order_id):
           pass

       async def get_open_positions(self):
           pass
   ```
4. Test thoroughly before live trading

### Running Tests

**Current State**: No tests yet (see ROADMAP.md #16)

**Planned**:
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Full test suite
pytest tests/

# With coverage
pytest --cov=. tests/
```

---

## Troubleshooting Guide

### Issue: Crypto.com API Returns 400 Error

**Location**: `/data/crypto_feed.py:163`
**Error Message**: `Client error '400 Bad Request' for url 'https://api.crypto.com/exchange/v1/public/get-candlestick?instrument_name=BTCUSD&timeframe=1h'`

**Possible Causes**:
1. Incorrect instrument name format
2. Invalid timeframe parameter
3. Missing required parameters

**Solutions**:
```python
# Try different formats:
"BTC_USD"   # Underscore format
"BTC-USD"   # Dash format
"BTCUSD"    # No separator (current)

# Check API documentation at:
# https://exchange-docs.crypto.com/exchange/v1/rest-ws/index.html
```

**Quick Fix**:
1. Read crypto_feed.py
2. Find all occurrences of instrument name construction
3. Update format based on API docs
4. Test with `await feed.get_ticker("BTC_USD")`

### Issue: Module Import Errors

**Error**: `ModuleNotFoundError: No module named 'xxx'`

**Solution**:
```bash
pip3 install -r requirements.txt
```

### Issue: Web Dashboard Not Accessible

**Check**:
1. Is server running?
   ```bash
   ps aux | grep "main.py web"
   ```
2. Is port 8000 in use?
   ```bash
   lsof -i :8000
   ```
3. Check logs:
   ```bash
   cat /tmp/claude/tasks/*.output | grep ERROR
   ```

**Restart**:
```bash
# Kill existing
pkill -f "main.py web"

# Restart
python3 main.py web
```

### Issue: AttributeError in LiveTrader

**Example**: `'AlertManager' object has no attribute 'AlertType'`

**Cause**: Missing imports

**Fix**:
```python
# In live_trader.py, ensure:
from monitoring.alerts import AlertManager, AlertType, AlertLevel, console_handler
```

---

## Current System State

### Running Services

**Web Dashboard**:
- Status: ✅ Running (as of last check)
- URL: http://localhost:8000
- Process ID: Check with `ps aux | grep main.py`
- Logs: `/tmp/claude/tasks/b2b6633.output`

**Live Trader**:
- Status: ✅ Running in background
- Update Interval: 30 seconds
- Symbols: ["BTCUSD"]
- Mode: Paper trading

### Recent Changes

1. ✅ Created web dashboard with FastAPI
2. ✅ Added light/dark/system theme support
3. ✅ Fixed AlertType/AlertLevel import issues
4. ✅ Removed pandas-ta dependency (installation issues)
5. ✅ Added websockets to requirements.txt

### Known Working Features

- ✅ Paper trading simulator
- ✅ Technical indicator calculation
- ✅ Signal generation
- ✅ Position management
- ✅ Risk management (position sizing, stop-loss, circuit breaker)
- ✅ PnL tracking
- ✅ Alert system
- ✅ Web dashboard UI
- ✅ Theme switching
- ✅ Console logging

### Known Issues

1. ❌ Crypto.com API integration (400 errors)
2. ❌ No database persistence
3. ❌ No real API keys configured
4. ⚠️ Limited error handling in some places
5. ⚠️ No tests

---

## Development Workflow

### When User Says "Continue" or "Next"

1. Check `ROADMAP.md` for next priority task
2. Look for 🔴 CRITICAL items first
3. Then 🟠 HIGH priority items
4. Choose something appropriate for the time available

**Likely Next Tasks**:
- Fix Crypto.com API integration
- Create .env file and configure API keys
- Set up Redis and PostgreSQL
- Add Forex market integration
- Implement sentiment analysis

### When User Reports an Error

1. Read the full error message
2. Identify the file and line number
3. Read the problematic file
4. Understand the root cause
5. Fix the issue
6. Test the fix
7. Restart affected services

### When Adding New Features

1. Check if it's in ROADMAP.md
2. Understand requirements
3. Design the solution
4. Implement incrementally
5. Test thoroughly
6. Update documentation
7. Add to README.md usage examples

### Code Style Guidelines

- Use async/await for I/O operations
- Add type hints to function signatures
- Write docstrings for classes and public methods
- Use loguru for logging
- Follow PEP 8 style guide
- Keep functions focused and small
- Use dataclasses for data structures
- Handle errors gracefully

---

## Testing Checklist

### Before Committing Changes

- [ ] Code runs without errors
- [ ] Imports are correct
- [ ] No syntax errors
- [ ] Logging messages are informative
- [ ] Error handling is comprehensive
- [ ] Configuration is parameterized (no hardcoded values)
- [ ] Documentation is updated
- [ ] README.md reflects changes if needed

### For New Features

- [ ] Works with paper broker
- [ ] Handles edge cases
- [ ] Integrates with existing components
- [ ] Has configurable parameters
- [ ] Logs important events
- [ ] Sends appropriate alerts
- [ ] Updates dashboard data

---

## Quick Reference: File Purposes

### Must-Read Files
| File | Why Read It |
|------|-------------|
| `Context.md` | Original project vision and goals |
| `README.md` | Usage instructions and examples |
| `ROADMAP.md` | What needs to be done next |
| `AI_CONTEXT.md` | This file - complete context |

### Core Logic Files
| File | Purpose |
|------|---------|
| `main.py` | Entry point, demo runners |
| `data/crypto_feed.py` | Market data fetching |
| `signals/technical.py` | Technical indicators |
| `strategy/signal_strategy.py` | Main trading strategy |
| `execution/order_manager.py` | Order coordination |
| `monitoring/live_trader.py` | Trading loop |
| `monitoring/web_dashboard.py` | Web interface |

### Configuration Files
| File | Purpose |
|------|---------|
| `requirements.txt` | Python dependencies |
| `config/config.py` | Config loader |
| `config/.env` | API keys (not created yet) |

---

## External Resources

### API Documentation
- **Crypto.com**: https://exchange-docs.crypto.com/exchange/v1/rest-ws/index.html
- **OANDA Forex**: https://developer.oanda.com/rest-live-v20/introduction/
- **Zerodha Kite**: https://kite.trade/docs/connect/v3/
- **NewsAPI**: https://newsapi.org/docs
- **Alpha Vantage**: https://www.alphavantage.co/documentation/

### Useful Libraries
- **pandas**: Data manipulation
- **numpy**: Numerical computing
- **httpx/aiohttp**: Async HTTP clients
- **fastapi**: Web framework
- **redis**: In-memory data store
- **sqlalchemy**: SQL ORM
- **loguru**: Better logging
- **pydantic**: Data validation

### Reference Projects
- **freqtrade**: Crypto trading bot
- **jesse-ai**: Clean algo framework
- **backtrader**: Backtesting library
- **quantconnect/lean**: Multi-asset engine

---

## Commands AI Assistants Should Know

### File Operations
```bash
# Find files
find . -name "*.py" | grep strategy

# Search in files
grep -r "class.*Strategy" . --include="*.py"

# Count lines
wc -l *.py

# View file
cat main.py

# Edit file
# Use Edit tool with old_string and new_string
```

### Python Operations
```bash
# Install dependencies
pip3 install -r requirements.txt

# Run scripts
python3 main.py

# Check Python version
python3 --version

# List installed packages
pip3 list
```

### Process Management
```bash
# Check running processes
ps aux | grep python3

# Kill process
kill -9 <PID>
pkill -f "main.py"

# Check port usage
lsof -i :8000
```

### Logs and Debugging
```bash
# View recent logs
tail -100 /tmp/claude/tasks/*.output

# Follow logs
tail -f /tmp/claude/tasks/*.output

# Search logs
grep ERROR /tmp/claude/tasks/*.output
```

---

## State Persistence

### Current Limitations
- ❌ No database - all data in memory
- ❌ Restart loses trade history
- ❌ PnL tracking resets on restart
- ❌ No strategy parameter history

### Planned Solutions (ROADMAP.md)
- Set up Redis for caching
- Set up PostgreSQL for persistence
- Implement data models
- Add migration system

---

## For AI Assistants: Best Practices

### Do's ✅
- Read ROADMAP.md before suggesting new features
- Check if web dashboard is running before starting it again
- Use existing patterns and conventions
- Add comprehensive error handling
- Update documentation when making changes
- Test changes before marking as complete
- Use async/await for I/O
- Log important events

### Don'ts ❌
- Don't blindly reinstall packages if not needed
- Don't assume API keys are configured
- Don't start multiple instances of web dashboard
- Don't make breaking changes without explaining
- Don't add dependencies without updating requirements.txt
- Don't hardcode values that should be in config
- Don't skip error handling

### When Uncertain
1. Ask the user for clarification
2. Read the relevant source files
3. Check the logs for errors
4. Review ROADMAP.md for context
5. Make informed suggestions

---

## Resuming After Long Break

### Checklist for AI Assistants

1. **Verify environment**:
   ```bash
   python3 --version
   pip3 list | grep -E "(pandas|fastapi|httpx)"
   ```

2. **Check current status**:
   ```bash
   ps aux | grep python3
   ls -la config/.env 2>/dev/null || echo "No .env file"
   ```

3. **Review recent changes**:
   ```bash
   git log --oneline -10  # If git repo
   ls -lt *.py | head -5  # Recently modified files
   ```

4. **Read context files**:
   - Context.md
   - README.md
   - ROADMAP.md
   - This file

5. **Ask user**: "What would you like to work on?"
   - If "continue" → Check ROADMAP.md for next priority
   - If "fix errors" → Check logs and debug
   - If specific feature → Implement it
   - If "status" → Report current state

---

## Project Metrics

### Codebase Size
- **Total Files**: ~20 Python files
- **Total Lines**: ~5,000+ lines
- **Modules**: 6 (data, signals, strategy, risk, execution, monitoring)
- **Classes**: 20+
- **Functions/Methods**: 150+

### Implementation Progress
- Phase 1: ✅ 100% Complete
- Phase 2: ✅ 100% Complete
- Phase 3: ✅ 100% Complete
- Phase 4: ✅ 100% Complete
- Phase 5: ⏳ 0% (Multi-market expansion)

### Test Coverage
- Unit Tests: ❌ 0%
- Integration Tests: ❌ 0%
- E2E Tests: ❌ 0%
- Manual Testing: ✅ Extensive

---

## Success Criteria

### Project is "Done" When:
- [x] All 4 phases complete
- [x] Paper trading works
- [x] Web dashboard operational
- [ ] Real broker integration working
- [ ] All markets integrated (Crypto, Forex, India, Commodities)
- [ ] Database persistence implemented
- [ ] Tests cover 80%+ of code
- [ ] Documentation complete
- [ ] Production deployment ready

### Current Status
**75% Complete** - Core functionality done, need real integrations and polish

---

## Summary for AI Assistants

**What This Is**: Automated multi-market trading bot with risk management, backtesting, and monitoring.

**What Works**: Everything in paper trading mode, web dashboard with themes.

**What Needs Work**: Real API integration, database persistence, additional markets, testing.

**Where to Start**: ROADMAP.md has prioritized tasks. Most urgent: Fix Crypto.com API, add .env config, set up database.

**How to Help**: Read context files, understand current state, pick next priority task from ROADMAP, implement carefully with error handling and documentation.

---

**End of AI Context Document**

*This document should enable any AI assistant to seamlessly resume work on this project with full understanding of its architecture, current state, and future direction.*
