# Trading Bot - Roadmap & Enhancement Plan

**Last Updated**: 2026-03-31 (Updated: Phase 5 Progress)
**Project Status**: Phase 5 In Progress - Sentiment Analysis & Multi-Source Data 🚀
**Next Major Milestone**: Database Persistence & Real Broker Integration

---

## 🎉 Recent Achievements (March 31, 2026)

Major features implemented since initial release:

### ✅ Sentiment Analysis System (COMPLETE)
- **NewsAPI Integration** - Real-time market news fetching
- **Alpha Vantage Integration** - News sentiment + Forex data
- **Sentiment Analyzer** - Keyword-based sentiment scoring
- **Strategy Enhancement** - Sentiment-aware trading signals
- **Market Context** - Global market sentiment tracking

### ✅ Multi-Source Data Infrastructure (COMPLETE)
- **CoinGecko Feed** - Free crypto price data (alternative to Crypto.com)
- **Factory Pattern** - Pluggable data provider system
- **Provider Configuration** - Environment-based provider selection
- **Unified Interface** - Consistent API across all data sources

### ✅ Enhanced Configuration System (COMPLETE)
- **Multi-Provider Support** - CoinGecko, Crypto.com, Alpha Vantage, NewsAPI
- **Forex Providers** - Alpha Vantage (implemented), OANDA/FXCM (planned)
- **News Providers** - NewsAPI (implemented), Alpha Vantage sentiment (implemented)
- **Execution Modes** - Paper trading (working), Real broker (planned)
- **Configuration Validation** - Automatic config validation on startup

### ✅ Sentiment-Aware Trading (COMPLETE)
- **Sentiment Scoring** - Positive/Negative/Neutral classification
- **Signal Adjustment** - Technical signals adjusted by sentiment (30% weight)
- **Entry Filtering** - Block trades against strong sentiment (-0.35 to +0.35 threshold)
- **Context Integration** - EUR/USD rates, news headlines in strategy context

### ✅ Database Persistence (v1.1 Foundation COMPLETE)
- **SQLAlchemy Integration** - Modular database layer with base configuration
- **Schema Design** - Models for Orders, Trades, Positions, Sentiment, and Performance
- **SQLite Support** - Default local persistence for development and testing
- **Trade History Repositories** - Decoupled repositories for Order and Trade entities
- **Broker Persistence** - Integrated PaperBroker with database for real-time trade logging
- **Market Data Cache** - Redis-backed caching for ticker and OHLCV data with JSON serialization
- **Performance Tracking** - Automatic equity and PnL snapshot persistence in PnLTracker
- **Hardening & Testing** - Unit tests implemented for all repositories with in-memory SQLite
- **Persistence Verified** - Successful test cycle for record saving and retrieval

### ✅ Multi-Source Data & Market Integration (v1.2 COMPLETE)
- **Unified Data Interface** - Abstract base class for all market providers
- **Market Registry** - Intelligent symbol routing (Crypto -> CoinGecko, Forex -> OANDA, Indian -> Shoonya, Global -> YFinance)
- **OANDA Integration** - Real-market Forex data implementation with REST API
- **Yahoo Finance Feed** - Free global market data fallback for stocks, indices, and commodities
- **Shoonya (Finvasia) Integration** - Full support for free Indian Market APIs (NSE, BSE, MCX) for both Data and Execution
- **Data Caching** - Integrated all providers with Redis for optimized performance

### ✅ Real-Time Monitoring & UI (v2.1 COMPLETE)
- **WebSocket Backend** - FastAPI WebSocket support for true real-time broadcasts
- **Live Dashboard Updates** - UI now updates PnL, trades, and signals instantly without polling
- **Broadcast Architecture** - PnLTracker now pushes updates to all connected web clients
- **Interactive Charts** - Integrated TradingView Lightweight Charts with real-time candle updates and theme support
- **JWT Authentication** - Secured dashboard with multi-layer auth (Login Screen, JWT, WebSocket Subprotocols)
- **Command Cockpit** - Added manual overrides (Pause/Resume Bot, Manual Position Close) with real-time UI synchronization

### ✅ Strategy Refinement & Tuning (v2.2 COMPLETE)
- **Parameterized Indicators** - Technical indicator engine now supports custom periods and thresholds
- **Symbol-Specific Tuning** - Strategies now load optimized parameters per symbol (BTC vs Reliance vs Forex)
- **Strategy Factory** - Centralized factory for creating and configuring strategies with tuned settings
- **Automated Tuning Script** - R&D script to find optimal indicator settings via iterative backtesting
- **Advanced Indicator Logic** - Integrated Ichimoku Cloud and Fibonacci Retracements into entry/exit decision making

### ✅ Intelligence & AI (v3.0 IN PROGRESS)
- **LSTM Price Prediction** - Deep Learning model predicts next-candle directional bias with "AI Confidence" scores
- **Predictive Strategy** - Integrated LSTM directional bias into signal scoring (20% weight)
- **Automated Model Training** - Tuning script now automatically trains neural networks on latest market data
- **LLM News Reasoning** - Integrated Local LLM (Ollama) to analyze news headlines and provide reasoned sentiment explanations
- **Market Correlation Matrix** - Automated Pearson correlation engine to detect and prevent over-exposure across similar assets

### ✅ Sophisticated Trading Features (v3.0 COMPLETE)
- **Multi-Timeframe Analysis (MTF)** - Triple Confirmation rule (5m entry confirmed by 1h and 1D major trends)
- **Institutional Indicators** - Integrated VWAP (Volume Weighted Average Price) and Volume Profile POC (Point of Control)
- **Trend Filtering** - Higher timeframe trend detection using SMA and Ichimoku crossovers
- **Statistical Arbitrage** - Implemented Pairs Trading strategy using cointegration and Z-Score divergence
- **Shoonya Options Support** - Enabled trading of Nifty/BankNifty Options with real-time Greeks (Delta, Theta, Gamma, Vega)

### ✅ Infrastructure & Reliability (v3.0 IN PROGRESS)
- **Dockerization** - Entire system containerized with Docker and orchestrated via Docker Compose
- **Prometheus Monitoring** - Real-time metrics exporter for PnL, trade volume, position count, and AI signal accuracy
- **One-Click Deployment** - Ready for 24/7 cloud execution with Bot, Redis, and PostgreSQL as a unified stack
- **Data Persistence** - Configured Docker volumes for persistent trade history and trained AI models

### 📊 New Files Added (Total: 5 major additions)
1. `data/coingecko_feed.py` - CoinGecko API adapter (201 lines)
2. `data/alpha_vantage_feed.py` - Alpha Vantage adapter (227 lines)
3. `data/newsapi_feed.py` - NewsAPI adapter (77 lines)
4. `data/factory.py` - Data provider factory (31 lines)
5. `signals/sentiment.py` - Sentiment analysis engine (67 lines)

### 🔧 Major Files Enhanced
1. `strategy/base_strategy.py` - Added market context support
2. `strategy/signal_strategy.py` - Sentiment-aware signal generation
3. `monitoring/live_trader.py` - Context refresh loop (30min intervals)
4. `config/config.py` - Multi-provider configuration
5. `monitoring/web_dashboard.py` - Ready for sentiment display

---

## Table of Contents
- [Recently Completed Features](#-recent-achievements-march-31-2026)
- [Pending Critical Tasks](#pending-critical-tasks)
- [High Priority Enhancements](#high-priority-enhancements)
- [Medium Priority Features](#medium-priority-features)
- [Performance & Optimization](#performance--optimization)
- [Quality Improvements](#quality-improvements)
- [Nice-to-Have Features](#nice-to-have-features)
- [Long-term Vision](#long-term-vision)

---

## 🎯 Immediate Next Steps (Recommended Order)

Based on recent progress, here's what to tackle next:

### A. Configure & Test New Features (Quick Win - 1 hour)
1. **Create .env file** with API keys for new providers:
   ```bash
   NEWS_API_KEY=your_key          # Get from newsapi.org
   ALPHA_VANTAGE_API_KEY=your_key # Get from alphavantage.co
   MARKET_DATA_PROVIDER=coingecko # Already set (free, no key needed)
   ```
2. **Test sentiment-aware trading** - Run live trader and verify sentiment in signals
3. **Check web dashboard** - Ensure sentiment context displays

### B. Database Persistence (High Impact - 1 day)
Set up Redis + PostgreSQL to persist:
- Trade history
- PnL snapshots
- Sentiment data
- Strategy parameters

### C. Web Dashboard Enhancement (High Visibility - 2-3 days)
Add to existing dashboard:
- Sentiment display panel
- News headlines widget
- Forex rates indicator
- Provider status monitoring

### D. Real Broker Integration (Production Ready - 1 week)
Choose one broker to start with:
- **OANDA** (Forex - easiest API)
- **Alpaca** (US stocks - simple REST API)
- **Interactive Brokers** (Multi-asset - complex but powerful)

---

## Pending Critical Tasks

### 1. API Configuration & Keys
**Priority**: 🔴 CRITICAL
**Effort**: Low (1-2 hours)

- [ ] Create `.env` file from `settings.example.env`
- [ ] Add Crypto.com API credentials (production)
- [ ] Test API connectivity with real credentials
- [ ] Document API rate limits and quotas
- [ ] Add API key rotation mechanism

**Why**: Currently running without real API keys, limiting functionality

### 2. Crypto Market Data (RESOLVED via CoinGecko)
**Priority**: ✅ RESOLVED (using CoinGecko as default)
**Effort**: Complete

- [x] **Switched to CoinGecko as default provider** ✅
- [x] CoinGecko provides free crypto data (no API key needed)
- [x] Factory pattern allows switching providers via config
- [ ] Optional: Fix Crypto.com API for alternative source
  - Debug 400 Bad Request error for BTCUSD endpoint
  - Verify correct instrument naming convention (BTC_USD vs BTCUSD)
  - Add fallback symbols (BTC_USDT, ETH_USD)
- [x] Retry logic with exponential backoff ✅ (in Alpha Vantage)

**Resolution**: System now uses CoinGecko by default (`MARKET_DATA_PROVIDER=coingecko`). Crypto.com remains as optional alternative. No API key required for CoinGecko free tier.

### 3. Database Setup
**Priority**: 🔴 CRITICAL
**Effort**: Medium (3-5 hours)

- [ ] Install and configure Redis for live data caching
- [ ] Set up PostgreSQL database schema
- [ ] Create SQLAlchemy models for:
  - Trades history
  - Position snapshots
  - PnL records
  - Strategy parameters
  - Backtest results
- [ ] Add database migrations (Alembic)
- [ ] Implement data persistence layer

**Why**: Currently all data is in-memory, lost on restart

---

## High Priority Enhancements

### 4. Multi-Market Integration
**Priority**: 🟠 HIGH
**Effort**: High (2-3 weeks)

**Original Project Goal** - Expand beyond crypto to multiple markets:

#### a) Forex Markets (IN PROGRESS)
- [x] **Alpha Vantage Forex Data** ✅ (EUR/USD implemented, more pairs available)
- [ ] Integrate OANDA REST API (for trading execution)
  - Real-time forex quotes
  - Historical data
  - Order execution
- [ ] Alternative: FXCM API integration
- [x] Add currency pair feeds (EUR/USD working) ✅
- [ ] Add more pairs (GBP/USD, USD/JPY, etc.)
- [ ] Implement forex-specific risk management
- [ ] Add pip calculation and position sizing

**Status**: Alpha Vantage provides free Forex quotes (EUR/USD live), used as market context indicator. Need OANDA/FXCM for actual Forex trading execution.

#### b) Indian Stock Markets
- [ ] Integrate Zerodha Kite API
  - NSE (National Stock Exchange)
  - BSE (Bombay Stock Exchange)
- [ ] Add Indian equity data feeds
- [ ] Implement circuit breaker rules (Indian market specific)
- [ ] Add tax calculations (STT, CTT, GST)
- [ ] Support for FnO (Futures & Options)

#### c) Commodities Markets
- [ ] MCX (Multi Commodity Exchange) integration
- [ ] Add commodity feeds (Gold, Silver, Crude Oil, etc.)
- [ ] Implement commodity-specific risk rules
- [ ] Add margin calculation for futures

### 5. Sentiment Analysis Engine ✅ **MOSTLY COMPLETE**
**Priority**: ✅ COMPLETE (with optional enhancements remaining)
**Effort**: ✅ Core implemented, optional: Medium (1 week)

- [x] Integrate NewsAPI for financial news ✅
- [x] Add Alpha Vantage news sentiment ✅
- [x] Implement NLP sentiment scoring ✅ (keyword-based)
- [x] Create sentiment-based trading signals ✅
- [ ] Add social media sentiment (Twitter/Reddit) - Optional
- [ ] Build sentiment dashboard visualization - Partially (context available, UI pending)
- [ ] Correlation analysis: sentiment vs price movement - Optional

**Status**: Core sentiment engine working! Strategy now uses sentiment to:
- Adjust signal strength (+/- 30% based on sentiment)
- Filter entries (block trades against strong sentiment)
- Display sentiment label and score in signals
- Refresh market context every 30 minutes

### 6. Advanced Risk Management
**Priority**: 🟠 HIGH
**Effort**: Medium (1 week)

- [ ] Portfolio-level risk management
  - Max portfolio heat (total risk exposure)
  - Correlation-based position sizing
  - Sector/asset class diversification rules
- [ ] Dynamic position sizing based on:
  - Recent win/loss streak
  - Current drawdown level
  - Market volatility (VIX integration)
- [ ] Implement trailing stops with ATR
- [ ] Add time-based stops (exit after X hours)
- [ ] Risk parity portfolio allocation

### 7. Production Web Dashboard Enhancements
**Priority**: 🟠 HIGH
**Effort**: Medium (1 week)

- [ ] Add authentication (JWT tokens)
- [ ] User management system
- [ ] Role-based access control (admin, viewer, trader)
- [ ] Real-time WebSocket price updates
- [ ] Interactive charts (TradingView/Chart.js)
- [ ] Order entry interface (manual trading)
- [ ] Strategy parameter tuning UI
- [ ] Backtest results visualization
- [ ] Performance comparison charts
- [ ] Mobile-responsive design improvements

---

## Medium Priority Features

### 8. Advanced Backtesting Framework
**Priority**: 🟡 MEDIUM
**Effort**: Medium (1-2 weeks)

- [ ] Walk-forward analysis
- [ ] Monte Carlo simulation
- [ ] Multi-asset portfolio backtesting
- [ ] Custom metrics and KPIs
- [ ] Benchmark comparison (SPY, BTC)
- [ ] Transaction cost analysis
- [ ] Slippage modeling improvements
- [ ] Report generation (PDF/HTML)
- [ ] Equity curve comparison tools

### 9. Strategy Library Expansion
**Priority**: 🟡 MEDIUM
**Effort**: High (2-3 weeks)

Implement additional trading strategies:

- [ ] **Mean Reversion**
  - Bollinger Band reversal
  - RSI oversold/overbought
- [ ] **Momentum Strategies**
  - Moving average crossovers (SMA/EMA)
  - MACD histogram
  - ADX trend strength
- [ ] **Breakout Strategies**
  - Support/resistance breakout
  - Volume breakout
  - Donchian channel
- [ ] **Arbitrage**
  - Cross-exchange arbitrage
  - Triangular arbitrage (forex)
- [ ] **Machine Learning**
  - LSTM price prediction
  - Random Forest signal classification
  - Reinforcement learning (DQN)
- [ ] **Multi-Timeframe Analysis**
  - Higher timeframe trend filter
  - Lower timeframe entry signals

### 10. Advanced Technical Indicators
**Priority**: 🟡 MEDIUM
**Effort**: Medium (1 week)

Add more technical analysis tools:

- [ ] Ichimoku Cloud
- [ ] Fibonacci retracements/extensions
- [ ] Elliott Wave analysis
- [ ] Volume profile
- [ ] Order flow analysis
- [ ] Market microstructure indicators
- [ ] Custom indicator builder

### 11. Notification & Alerting System
**Priority**: 🟡 MEDIUM
**Effort**: Low (2-3 days)

- [ ] Telegram bot configuration guide
- [ ] Email alerts (SendGrid/AWS SES)
- [ ] SMS notifications (Twilio)
- [ ] Webhook integrations (Zapier, IFTTT)
- [ ] Discord notifications
- [ ] Slack integration
- [ ] Push notifications (mobile app)
- [ ] Alert templates and customization

### 12. Real Broker Integrations
**Priority**: 🟡 MEDIUM
**Effort**: High (2-4 weeks)

Move beyond paper trading:

- [ ] Interactive Brokers API
- [ ] Alpaca API (US stocks)
- [ ] Binance API (crypto)
- [ ] Kraken API (crypto)
- [ ] TD Ameritrade API
- [ ] Add order type support:
  - Market orders
  - Limit orders
  - Stop-loss orders
  - Trailing stops
  - OCO (One-Cancels-Other)
  - Bracket orders
- [ ] Order status monitoring
- [ ] Trade reconciliation

---

## Performance & Optimization

### 13. Code Performance
**Priority**: 🟡 MEDIUM
**Effort**: Medium (1 week)

- [ ] Profile slow code paths
- [ ] Optimize data frame operations
- [ ] Add async/await throughout
- [ ] Implement connection pooling
- [ ] Cache frequently accessed data
- [ ] Batch database operations
- [ ] Add Redis caching layer
- [ ] Optimize indicator calculations
- [ ] Parallel strategy execution

### 14. Scalability Improvements
**Priority**: 🟡 MEDIUM
**Effort**: High (2-3 weeks)

- [ ] Microservices architecture
  - Data ingestion service
  - Strategy execution service
  - Risk management service
  - Order execution service
- [ ] Message queue (RabbitMQ/Kafka)
- [ ] Load balancing
- [ ] Horizontal scaling support
- [ ] Distributed backtesting
- [ ] Multi-instance coordination

### 15. Resource Optimization
**Priority**: 🟢 LOW
**Effort**: Medium (3-5 days)

- [ ] Memory usage optimization
- [ ] Reduce API call frequency
- [ ] Implement data compression
- [ ] Add data cleanup/archival
- [ ] Optimize log file sizes
- [ ] Docker container optimization

---

## Quality Improvements

### 16. Testing Suite
**Priority**: 🟠 HIGH
**Effort**: High (2-3 weeks)

- [ ] Unit tests for all modules
  - Strategies
  - Risk management
  - Indicators
  - Brokers
  - Order management
- [ ] Integration tests
- [ ] End-to-end tests
- [ ] Performance tests
- [ ] Load tests
- [ ] Mocking for external APIs
- [ ] Test coverage reporting
- [ ] Continuous integration (GitHub Actions)

### 17. Code Quality & Documentation
**Priority**: 🟡 MEDIUM
**Effort**: Medium (1 week)

- [ ] Add type hints everywhere
- [ ] Docstring improvements
- [ ] API documentation (Sphinx)
- [ ] Architecture diagrams
- [ ] Sequence diagrams for workflows
- [ ] Code linting (pylint, flake8)
- [ ] Code formatting (black)
- [ ] Pre-commit hooks
- [ ] Contributing guidelines

### 18. Error Handling & Resilience
**Priority**: 🟠 HIGH
**Effort**: Medium (3-5 days)

- [ ] Comprehensive exception handling
- [ ] Graceful degradation
- [ ] Circuit breaker pattern
- [ ] Retry mechanisms with backoff
- [ ] Dead letter queues
- [ ] Health checks
- [ ] Watchdog timers
- [ ] Auto-recovery procedures

### 19. Logging & Monitoring
**Priority**: 🟡 MEDIUM
**Effort**: Low (2-3 days)

- [ ] Structured logging (JSON)
- [ ] Log aggregation (ELK stack)
- [ ] Metrics collection (Prometheus)
- [ ] APM integration (DataDog, New Relic)
- [ ] Custom metrics dashboard
- [ ] Alerting thresholds
- [ ] Performance monitoring
- [ ] Distributed tracing

---

## Nice-to-Have Features

### 20. Machine Learning Integration
**Priority**: 🟢 LOW
**Effort**: Very High (1-2 months)

- [ ] Feature engineering pipeline
- [ ] Model training infrastructure
- [ ] Hyperparameter optimization
- [ ] Model versioning and deployment
- [ ] A/B testing framework
- [ ] Explainable AI for decisions
- [ ] Automated model retraining

### 21. Social Trading Features
**Priority**: 🟢 LOW
**Effort**: High (3-4 weeks)

- [ ] Copy trading functionality
- [ ] Strategy marketplace
- [ ] Performance leaderboards
- [ ] Social feeds
- [ ] Strategy sharing
- [ ] Community ratings/reviews

### 22. Mobile Application
**Priority**: 🟢 LOW
**Effort**: Very High (2-3 months)

- [ ] React Native or Flutter app
- [ ] Portfolio monitoring
- [ ] Trade notifications
- [ ] Manual trade execution
- [ ] Strategy controls
- [ ] Performance charts

### 23. Advanced Analytics
**Priority**: 🟢 LOW
**Effort**: High (3-4 weeks)

- [ ] Portfolio attribution analysis
- [ ] Risk decomposition
- [ ] Factor analysis
- [ ] Correlation matrices
- [ ] Market regime detection
- [ ] Scenario analysis
- [ ] Stress testing

---

## Long-term Vision

### Phase 5: Enterprise Features (3-6 months)

- [ ] Multi-user support
- [ ] White-label solution
- [ ] API for third-party integrations
- [ ] Strategy marketplace
- [ ] Managed accounts support
- [ ] Regulatory compliance tools
- [ ] Audit trail and reporting
- [ ] Client portal

### Phase 6: AI-Powered Trading (6-12 months)

- [ ] Reinforcement learning agents
- [ ] Natural language strategy builder
- [ ] Autonomous strategy optimization
- [ ] Market regime adaptation
- [ ] Sentiment-driven trading
- [ ] News-based event trading
- [ ] Computer vision for chart patterns

---

## Quick Wins (Can Implement This Week)

### Immediate Improvements
- [x] Web dashboard with theme support (DONE)
- [ ] Fix Crypto.com API instrument names
- [ ] Add more error handling
- [ ] Create .env configuration
- [ ] Add more example strategies
- [ ] Improve logging output
- [ ] Add health check endpoint
- [ ] Create Docker setup
- [ ] Add CLI commands for common tasks
- [ ] Generate sample backtest reports

---

## 🟢 Known Working Features

### Data Sources
- ✅ **CoinGecko** - Free crypto data (BTC, ETH, SOL, XRP, ADA, DOGE, BNB, AVAX, MATIC)
- ✅ **Alpha Vantage** - Forex rates (EUR/USD) + News sentiment
- ✅ **NewsAPI** - Market news search with customizable queries
- ⚠️ **Crypto.com** - Available but has endpoint issues (use CoinGecko instead)

### Trading Features
- ✅ **Technical Analysis** - RSI, MACD, Bollinger Bands, Moving Averages
- ✅ **Sentiment Analysis** - Keyword-based scoring (Positive/Negative/Neutral)
- ✅ **Sentiment-Aware Signals** - Adjusts strength by 30%, filters extreme sentiment
- ✅ **Paper Trading** - Full simulator with fees and slippage
- ✅ **Position Management** - Entry, exit, stop-loss, take-profit
- ✅ **Risk Management** - Position sizing, circuit breaker, stop-loss
- ✅ **PnL Tracking** - Real-time profit/loss calculation
- ✅ **Alert System** - Console alerts (Telegram ready, needs token)

### Monitoring
- ✅ **Web Dashboard** - FastAPI server with light/dark themes
- ✅ **Live Trading Loop** - Automated 60-second update cycle
- ✅ **Context Refresh** - News/sentiment update every 30 minutes
- ✅ **Performance Metrics** - Sharpe, Sortino, win rate, profit factor

### Configuration
- ✅ **Multi-Provider System** - Switch data sources via environment variables
- ✅ **Factory Pattern** - Easy to add new providers
- ✅ **Config Validation** - Automatic validation on startup
- ✅ **Environment-Based** - .env file support

---

## Known Issues & Bugs

### Current Bugs
1. ~~**Crypto.com API 400 Error**~~ - **RESOLVED** by using CoinGecko as default
   - ~~Issue: Incorrect instrument name format~~
   - Resolution: Switched to CoinGecko, works out of the box

2. ~~**PnL Tracker Initial Balance**~~ - **RESOLVED**
   - ~~Issue: AttributeError on 'initial_balance'~~
   - Resolution: Fixed in recent updates

3. **Missing .env File Warning** - Expected behavior
   - Not a bug: System works with defaults
   - Action: Create .env for API keys when ready

4. **pandas-ta Removed** - Technical indicators may be limited
   - Status: Core indicators (RSI, MACD, BB) implemented manually
   - Optional: Re-add pandas-ta or use ta-lib for advanced indicators

### Technical Debt
- [ ] Remove duplicate PnLTracker instances
- [ ] Consolidate AlertManager initialization
- [ ] Refactor main.py demo functions
- [ ] Extract hardcoded values to config
- [ ] Standardize error messages
- [ ] Add input validation everywhere

---

## Suggested Tools & Libraries

### Additional Dependencies
- **ta-lib** - More technical indicators
- **ccxt** - Multi-exchange crypto trading
- **yfinance** - Free stock data
- **scikit-learn** - Machine learning
- **tensorflow/pytorch** - Deep learning
- **celery** - Distributed task queue
- **dramatiq** - Alternative task queue
- **streamlit** - Quick data apps
- **plotly** - Interactive charts
- **dash** - Full dashboard framework

### Infrastructure
- **Docker** - Containerization
- **Kubernetes** - Orchestration
- **Nginx** - Reverse proxy
- **Let's Encrypt** - SSL certificates
- **Prometheus + Grafana** - Monitoring
- **ELK Stack** - Logging
- **Redis** - Caching
- **PostgreSQL** - Database
- **TimescaleDB** - Time-series data

---

## Contributing

When working on items from this roadmap:

1. Create a new branch for your feature
2. Update this document to mark items as in-progress
3. Add tests for new functionality
4. Update documentation
5. Submit PR with reference to roadmap item
6. Move completed items to CHANGELOG.md

---

## Priority Legend

- 🔴 **CRITICAL** - Blocks core functionality, needs immediate attention
- 🟠 **HIGH** - Important for production use, plan for next sprint
- 🟡 **MEDIUM** - Nice to have, improves user experience
- 🟢 **LOW** - Future enhancement, not urgent

---

## 📝 Implementation Notes (March 31, 2026)

### What Just Got Built

**Phase 5A: Sentiment-Aware Trading System** (Implemented Today)

1. **Data Layer Expansion**:
   - Added 3 new data feed adapters (CoinGecko, Alpha Vantage, NewsAPI)
   - Implemented factory pattern for provider selection
   - Made CoinGecko the default (free, no API key, reliable)

2. **Sentiment Engine**:
   - Keyword-based sentiment analyzer (67 lines)
   - Positive/negative keyword dictionaries
   - Article aggregation and scoring
   - Sentiment label classification (BULLISH/BEARISH/NEUTRAL)

3. **Strategy Enhancement**:
   - Market context support in BaseStrategy
   - Sentiment-aware signal generation
   - 30% sentiment weight in signal strength
   - Entry filtering based on extreme sentiment

4. **Live Trading Integration**:
   - Context refresh loop (30-minute intervals)
   - Multi-source news aggregation
   - Symbol alias mapping for news queries
   - EUR/USD forex rate tracking
   - Provider status monitoring

5. **Configuration System**:
   - Environment-based provider selection
   - Support for multiple API keys
   - Config validation
   - Execution mode switching (paper/real)

**Files Modified**: 8 existing files
**Files Created**: 5 new files
**Total New Lines**: ~600 lines of code
**Testing**: Manual testing in paper trading mode
**Status**: ✅ Working, ready for use

### Next Session Goals

1. **Test with API Keys** (30 min)
   - Get free API keys from NewsAPI and Alpha Vantage
   - Create .env file
   - Run live trader and verify sentiment data flows

2. **Dashboard Enhancement** (2 hours)
   - Add sentiment display panel
   - Show news headlines
   - Display provider status
   - Add forex rate widget

3. **Database Setup** (4 hours)
   - Install Redis and PostgreSQL
   - Create database schema
   - Implement data persistence
   - Test data recovery after restart

---

**Note**: This roadmap is a living document. Update it as priorities change and new requirements emerge.
