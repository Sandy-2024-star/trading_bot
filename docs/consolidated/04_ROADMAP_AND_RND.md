# 04 ROADMAP AND RND: Development & Implementation Plan

**Last Updated**: 2026-04-01
**Project Status**: Phase 5 In Progress - Intelligence, AI & Advanced Execution 🚀

---

## 1. Development Roadmap & Phases

The project follows a modular evolution from a basic paper trader to an institutional-grade multi-market system.

### ✅ Phase 1: Foundation & Persistence (v1.1 - COMPLETE)
- **SQLAlchemy Integration**: Modular database layer (PostgreSQL/SQLite).
- **Trade History**: Decoupled repositories for Orders, Trades, and Positions.
- **Market Data Cache**: Redis-backed caching for tickers and OHLCV data.
- **Performance Tracking**: Automatic equity and PnL snapshot persistence.

### ✅ Phase 2: Multi-Market Integration (v1.2 - COMPLETE)
- **Unified Data Interface**: Abstract base class for all market providers.
- **Market Registry**: Intelligent symbol routing (Crypto -> CoinGecko, Forex -> OANDA, Indian -> Shoonya, Global -> YFinance).
- **Shoonya (Finvasia)**: Support for Indian Markets (NSE, BSE, MCX) for Data and Execution.
- **OANDA & YFinance**: Real-market Forex and Global stock data implementation.

### ✅ Phase 3: UI & Monitoring (v2.1 - COMPLETE)
- **WebSocket Backend**: FastAPI support for real-time broadcasts.
- **Interactive Charts**: Integration of TradingView Lightweight Charts.
- **Security**: JWT Authentication for dashboard access.
- **Command Cockpit**: Manual overrides (Pause/Resume, Manual Close).

### ✅ Phase 4: Strategy Refinement & Tuning (v2.2 - COMPLETE)
- **Parameterized Indicators**: Custom periods and thresholds for all indicators.
- **Automated Tuning**: R&D scripts for optimizing parameters via backtesting.
- **Advanced Logic**: Integration of Ichimoku Cloud and Fibonacci Retracements.

### 🚀 Phase 5: Intelligence & Enterprise Features (v3.0 - IN PROGRESS)
- **LSTM Price Prediction**: Deep Learning for next-candle directional bias.
- **LLM News Reasoning**: Local LLM (Ollama) for sentiment explanation.
- **MTF Analysis**: Triple Confirmation rule (5m, 1h, 1D).
- **Institutional Tools**: VWAP, Volume Profile POC, and Correlation Matrices.
- **Infrastructure**: Full Dockerization and Prometheus monitoring.

---

## 2. Current Task Status (Task List)

### 🟢 v1.1 - v1.2: Core Infrastructure (COMPLETE ✅)
- [x] Design and implement Database Schema & Models.
- [x] Integrate `PaperBroker` with persistence repositories.
- [x] Setup Redis Connection Manager for market data caching.
- [x] Implement Multi-Market Routing (Crypto, Forex, Indian, Global).
- [x] Shoonya Broker integration for real execution.

### 🔵 v2.1 - v2.2: UI & Strategy (COMPLETE ✅)
- [x] WebSocket broadcast for real-time PnL/Trade updates.
- [x] Secure JWT Dashboard Login.
- [x] Centralized `Strategy Factory`.
- [x] Automated Parameter Tuning Script.
- [x] Advanced Indicators: Ichimoku & Fibonacci.

### 🟡 v3.0: Intelligence & Advanced Execution (IN PROGRESS 🚀)
- [x] **LSTM Model**: Directional prediction engine.
- [x] **News Reasoner**: Local LLM sentiment analysis.
- [x] **Correlation Engine**: Portfolio risk analysis.
- [x] **MTF Analysis**: 5m/1h/1D trend filtering.
- [x] **Statistical Arbitrage**: Pairs Trading strategy.
- [x] **Options Support**: Shoonya Greeks and Option Chain.
- [x] **Dockerization**: Full stack orchestration.
- [x] **Prometheus**: Real-time metrics exporter.
- [ ] **Grafana Dashboard**: Visualizing Prometheus metrics.
- [ ] **Parameter Editor**: Browser-based strategy adjustment.

---

## 3. RND: Chart & Execution Integration Plan

### Objective
Build a validated entry/exit flow that treats chart review, strategy logic, and risk management as one consistent trading path.

### Selected Stack: TradingView Lightweight Charts
- **Why**: Lightweight, fast, and fits perfectly into the FastAPI/HTML dashboard.
- **Usage**: OHLC Candles, Entry/Exit markers, Stop-Loss/Take-Profit horizontal lines.
- **Boundary**: The strategy engine is the Source of Truth; the chart is for visualization and explanation.

### Step-by-Step Implementation Plan
1.  **Chart Access Foundation**: Create a reliable data workflow (OHLCV) for target symbols.
2.  **Entry Setup Definition**: Define deterministic entry rules (Signal + Sentiment + Candle Close).
3.  **Stop-Loss Design**: Standardize on ATR or Fixed Percentage models.
4.  **Take-Profit & Exit Logic**: Separate defensive stops from profit-taking and reverse-signal exits.
5.  **Trade Lifecycle Simulation**: End-to-end R&D runner to simulate the full path before production.
6.  **Production Promotion**: Move validated logic into `main.py`, `strategy/`, and `risk/`.

### Chart Data Contract (Requirements)
- **Candle Shape**: `timestamp`, `open`, `high`, `low`, `close`, `volume`.
- **Markers**: For Entry/Exit points (`time`, `position`, `color`, `shape`, `text`).
- **Price Lines**: For SL/TP levels (`title`, `price`, `color`, `lineStyle`).
- **Minimum History**: 100 candles for proper indicator calculation and visual review.

### Backend/Frontend Payload Split
- **Backend (Python)**: Normalizes data, calculates overlays, and emits a structured `decision` payload.
- **Frontend (JS)**: Renders the chart and applies markers/lines based on the backend payload.
- **Volume Note**: CoinGecko volume data is currently limited; volume-based logic should be used cautiously.

---

## 4. Technical Debt & Known Issues

### ⚠️ Known Issues
- **Crypto.com API**: Resolved by using CoinGecko as the default.
- **Missing .env**: System works with defaults but requires `.env` for full API functionality.
- **Pandas-TA**: Replaced with manual core indicator implementations for stability.

### 🛠 Technical Debt
- [ ] Remove duplicate `PnLTracker` instances.
- [ ] Consolidate `AlertManager` initialization.
- [ ] Standardize error messages across data providers.
- [ ] Implement input validation for all configuration entry points.

---

## 5. Long-term Vision

### Phase 6: Enterprise & AI (6-12 Months)
- **Managed Accounts**: Support for multi-user/client portals.
- **Autonomous Optimization**: Reinforcement learning for strategy adaptation.
- **Computer Vision**: Identifying chart patterns via AI.
- **Mobile Application**: React Native/Flutter for remote monitoring and controls.
