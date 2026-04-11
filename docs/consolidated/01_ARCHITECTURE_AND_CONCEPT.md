# 01_ARCHITECTURE_AND_CONCEPT.md - Multi-Market Trading Bot

## 🚀 Project Overview & Vision

The **Enterprise Trading Bot (v3.0)** is an institutional-grade automated multi-market trading system designed to trade across Cryptocurrency, Forex, Indian Markets (NSE/BSE), and Commodities (MCX). Built with a strictly decoupled 6-layer architecture, it combines technical analysis, real-time news sentiment, and AI-driven price prediction to execute high-conviction trades while prioritizing capital preservation.

### Core Objectives
- **Cross-Market Trading**: Unified execution across disparate asset classes.
- **Intelligent Signal Generation**: Fusion of technical indicators, news sentiment, and cross-market correlation.
- **Robust Risk Management**: Mandatory position sizing, stop-losses, and automated circuit breakers.
- **Scalable Execution**: High-fidelity backtesting, paper trading, and real-time live trading.
- **Full Observability**: Real-time monitoring via PnL dashboards, Telegram alerts, and Prometheus metrics.

### Guiding Principles
1. **Safety First**: Risk management logic always precedes profitability checks.
2. **Incremental Deployment**: Rigorous testing from backtest to paper trading before live capital.
3. **Modularity**: Every layer is decoupled; data feeds can be swapped without affecting strategy logic.
4. **Fail-Safe Design**: Automatic halts on anomalies (e.g., high drawdown, consecutive losses).
5. **Observability**: Complete visibility into every decision made by the system.

---

## 🛠 Core Technology Stack (100% FREE Stack)

The project is architected to run on a completely free, high-performance tech stack:

| Category | Technology |
| :--- | :--- |
| **Language** | Python 3.10+ |
| **Market Data (FREE)** | `yfinance` (Stocks/Forex), `ccxt` (Crypto), `CoinGecko` |
| **News/Sentiment** | `Tavily Search` (AI-powered), `Exa Search`, Local LLM (LiteLLM/Ollama) |
| **Database** | `PostgreSQL` (Production), `SQLite` (Dev), `SQLAlchemy` ORM |
| **Caching** | `Redis` (High-speed market data caching) |
| **API Framework** | `FastAPI` (Backend/Internal Dashboard) |
| **AI/Analysis** | `TensorFlow` (LSTM), `pandas-ta` (Technical Indicators) |
| **Infrastructure** | `Docker` & `Docker Compose`, `MCP Servers` (Postgres, Tavily, Github) |
| **Logging/Alerts** | `loguru`, `Telegram API`, `Prometheus` |

---

## 🏗 System Architecture (The 6-Layer Design)

The system follows a modular, decoupled 6-layer architecture to ensure scalability and maintainability.

### 1. Data Ingestion Layer (`/data/`)
- **Market Feeds**: Multi-market adapters (`MT5Feed`, `ShoonyaFeed`, `OandaFeed`, `YFinanceFeed`, `CCXTFeed`).
- **News APIs**: Retrieval from NewsAPI, Alpha Vantage, and AI-powered neural search (Tavily/Exa).
- **Caching**: Uses Redis for low-latency access to the latest ticker and orderbook data.

### 2. Analysis & AI Engine (`/analysis/`, `/ai/`, `/signals/`)
- **Technical Indicators**: RSI, MACD, Ichimoku, Fibonacci, VWAP, and Volume Profile.
- **AI Models**: LSTM for price prediction and LLM News Reasoning for fundamental sentiment.
- **Correlation**: Pearson Correlation Matrix to identify cross-market arbitrage and hedging.

### 3. Strategy Layer (`/strategy/`)
- **Logic**: Multi-Timeframe (MTF) confirmed trade logic, Pairs Trading, Mean Reversion, and Options strategies.
- **Framework**: `BaseStrategy` abstract class handles position tracking and signal analysis.

### 4. Risk Management Layer (`/risk/`)
- **Position Sizer**: Supports 5 methods (Fixed, % Equity, Risk-Based, Kelly Criterion, Volatility).
- **Stop-Loss Manager**: Fixed %, ATR-based, S/R levels, and Trailing Stops.
- **Circuit Breaker**: Automatic halts for daily loss limits, consecutive losses, or max drawdown.

### 5. Execution Layer (`/execution/`)
- **Brokers**: Unified `BaseBroker` interface for `PaperBroker` and live adapters (MT5, Crypto.com, Zerodha).
- **Order Manager**: Multi-leg atomic order management and repository-based persistence.
- **Backtester**: High-fidelity historical simulation with realistic slippage and fee modeling.

### 6. Monitoring & Alerting (`/monitoring/`)
- **PnL Tracker**: Real-time realized/unrealized PnL tracking and equity curve generation.
- **Alert System**: 4 levels (INFO to CRITICAL) with pluggable handlers (Console, Telegram).
- **Dashboard**: FastAPI-powered web interface and real-time console summaries.

---

## 📝 Design Philosophy & Mandates

### Implementation Mandates (STRICT)
- **Atomic Execution**: All multi-leg trades (e.g., Pairs) must be executed atomically or rolled back.
- **AI Consistency**: New symbols must have LSTM models trained via the tuning pipeline before activation.
- **Resilience**: A watchdog (`_check_connections`) maintains connectivity to all data feeds and brokers.
- **Persistence**: All trades, orders, and performance snapshots are saved to the database (Postgres/SQLite).

### Technical Integrity
- **Types & Linters**: Strict adherence to Python type hints and PEP 8 standards.
- **Testing**: No code change is complete without passing unit tests (`pytest`) and a 1-year historical backtest.
- **Risk-First**: Position sizing defaults to a "Risk-Based" method (e.g., 2% risk per trade) requiring a mandatory Stop-Loss.

---

## 🗺 Project Roadmap

| Version | Focus | Status |
| :--- | :--- | :--- |
| **v1.0** | Core 4 Phases (Data, Strategy, Execution, Monitoring) | ✅ Complete |
| **v1.1** | Data Persistence & Database Stability | ✅ Complete |
| **v1.2** | Multi-Market Data Integration (Forex/Indian/Commodities) | ✅ Complete |
| **v2.0** | Sentiment Analysis & AI Intelligence | ✅ Complete |
| **v2.1** | Web Dashboard (FastAPI + React) | ⏳ In Progress |
| **v3.0** | Production Hardening & Enterprise Monitoring | 📅 Planned |

---

## 💾 Operational Guidelines
- **Development**: Core logic resides in `trading_bot/`, experiments in `RND/experiments/`.
- **Deployment**: Managed via `docker-compose up --build -d`.
- **Testing**: Run comprehensive tests with `pytest trading_bot/tests/`.
- **Maintenance**: Database migrations are handled via Alembic; backups are scheduled daily.
