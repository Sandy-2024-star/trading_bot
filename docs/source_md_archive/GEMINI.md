# GEMINI.md - Multi-Market Trading Bot Context

This document provides essential context and instructions for AI assistants working on the Enterprise Trading Bot project (v3.0).

## 🚀 Project Overview

**Purpose**: An institutional-grade automated multi-market trading system (Crypto, Forex, Indian Markets, Global Stocks) built with a modular 5-layer architecture.
**Core Tech**: Python 3.10+, TensorFlow (AI), FastAPI (UI), Redis (Cache), SQLAlchemy (PostgreSQL/SQLite).

---

## 🏗 System Architecture (Refined v3.0)

The project follows a strictly decoupled 5-layer design:

1.  **Core Abstractions (`/core/`)**: Base classes for all feeds, brokers, and strategies.
2.  **Data Ingestion (`/data/`)**: Multi-market adapters (`ShoonyaFeed`, `OandaFeed`, `YFinanceFeed`, `CoinGeckoFeed`). Uses Redis for high-speed caching.
3.  **Analysis & AI (`/analysis/`, `/ai/`)**: 
    *   `ai/`: LSTM Price Prediction and LLM News Reasoning (Ollama).
    *   `analysis/`: Pearson Correlation Matrix and Prometheus metrics.
    *   `signals/`: Advanced Technical Indicators (Ichimoku, Fibonacci, VWAP, Volume Profile).
4.  **Strategy (`/strategy/`)**: Multi-Timeframe (MTF) confirmed trade logic. Supports Technical, Pairs Trading, and Mean Reversion.
5.  **Execution & Risk (`/execution/`, `/risk/`)**: 
    *   `execution/`: Multi-leg atomic order management and repository-based persistence.
    *   `risk/`: Portfolio Heat limits, Trailing Stops, and Circuit Breakers.

---

## 💾 Persistence Layer

-   **Repositories**: Found in `execution/repositories/` and `monitoring/repositories/`.
-   **Database**: Supports PostgreSQL (production) and SQLite (dev).
-   **Monitoring**: Real-time WebSockets and Prometheus metrics (`port 9090`).

---

## 🛠 Operational Commands

-   **Dashboard**: `python trading_bot/main.py web`
-   **Deployment**: `docker-compose up --build -d`
-   **Tuning**: `python trading_bot/RND/experiments/tune_strategy.py SYMBOL`
-   **Tests**: `pytest trading_bot/tests/`

---

## 📝 Development Guidelines

### 1. File Organization (STRICT)
-   **Core Logic**: Always place in the appropriate modular subfolder within `trading_bot/`.
-   **Experimental**: Put temporary or R&D scripts in `trading_bot/RND/experiments/`.
-   **Archive**: Never delete history; move redundant or old logic to `trading_bot/archive/`.
-   **Documentation**: Centralized in `trading_bot/docs/`.

### 2. Implementation Mandates
-   **Atomic Execution**: All multi-leg trades (Pairs) must be executed atomically.
-   **AI Consistency**: New symbols should have their LSTM models trained via the tuning script.
-   **Resilience**: Use the `_check_connections` watchdog in the main loop.

**Last Restructured**: 2026-04-01
