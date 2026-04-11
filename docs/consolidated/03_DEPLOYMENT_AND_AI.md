# Deployment, AI, and Agent Operations Guide 🚀

This comprehensive guide covers the deployment architecture, database management, AI integration, and agent-assisted development workflows for the Multi-Market Trading Bot.

---

## 1. Docker Deployment Architecture

The system is designed to run as a multi-container application using Docker Compose, ensuring consistency across development and production environments.

### Quick Start
1. **Configure Environment**: Ensure `trading_bot/config/.env` is populated with your API keys.
2. **Build and Start**:
   ```bash
   docker-compose up --build -d
   ```
3. **Verify**: Access the dashboard at `http://localhost:8000`.

### Operational Commands
| Action | Command |
|--------|---------|
| View Logs | `docker logs -f trading_bot` |
| Stop System | `docker-compose down` |
| Rebuild Bot Only | `docker-compose up --build -d bot` |
| Postgres Shell | `docker exec -it trading_bot_postgres psql -U postgres -d trading_bot` |

### Persistence Mapping
- **Trade History**: Stored in Docker volume `postgres_data`.
- **AI Models**: Mapped to local `./data/models` directory.
- **Configurations**: Local `./trading_bot/config/.env` is synced with the container.

---

## 2. Database Migration & Initialization

The bot supports both **SQLite** (default for development) and **PostgreSQL** (recommended for production).

### Schema Initialization
To create the database schema for the first time:
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/trading_bot
python3 -c "from database import init_db; init_db(); print('Database initialized!')"
```

### PostgreSQL Migration
1. Set `POSTGRES_PASSWORD` in `.env` to trigger the switch from SQLite.
2. Configure `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, and `POSTGRES_USER`.
3. Run the initialization command above to create tables in the Postgres instance.

### Schema Management (Alembic)
For complex schema changes, use Alembic:
- **Create Migration**: `alembic revision --autogenerate -m "Description"`
- **Apply Migration**: `alembic upgrade head`

---

## 3. AI & Market Sentiment Engine

The bot uses a multi-layered approach to AI, integrating technical signals with natural language sentiment.

### Sentiment-Aware Trading (Phase 5)
- **Data Sources**: CoinGecko (Crypto), Alpha Vantage (Forex/News), NewsAPI.
- **Sentiment Logic**: Keyword-based scoring (Positive: beat, bullish, rally; Negative: crash, decline, ban).
- **Signal Adjustment**: Technical signals are adjusted by ±30% based on sentiment scores.
- **Risk Filtering**: 
  - Blocks **BUY** if sentiment <= -0.35 (Strong Bearish).
  - Blocks **SELL** if sentiment >= 0.35 (Strong Bullish).

### AI Model Management
- **LSTM Price Prediction**: Models are stored in `/data/models/`.
- **LLM Reasoning**: Integrated via Ollama for news reasoning.
- **Tuning**: New symbols should have models trained via `python trading_bot/RND/experiments/tune_strategy.py SYMBOL`.

---

## 4. MCP Servers Integration

Model Context Protocol (MCP) servers enhance the bot's capabilities when used with AI IDEs like Cursor or OpenCode.

### Available MCP Servers
| Server | Use Case | Setup |
|--------|----------|-------|
| **PostgreSQL** | Query trade history, calculate win rates, PnL analysis. | `npx -y @modelcontextprotocol/server-postgres` |
| **Tavily** | AI-powered news search and sentiment analysis. | `npx -y @tavily/mcp-server` |
| **Exa** | Neural search for financial research and signal validation. | `npx -y @exa/mcp-server` |
| **GitHub** | Strategy versioning and log management. | `npx -y @github/mcp-server` |

---

## 5. AI Agent Context & Memory

Agents working on this codebase MUST adhere to specific memory and architectural rules to ensure system integrity.

### Memory Rules
1. **Local Project Context**: Project-specific specs, TODOs, and architectural decisions should be appended to the "Project Log" in `AGENTS.md`.
2. **Global Context**: Use `save_memory` only for universal user preferences.

### Agent Workflow
- **Research**: Use `grep_search` and `glob` to map the 5-layer architecture before editing.
- **Execution**: Follow the **Plan -> Act -> Validate** cycle.
- **Validation**: Run `pytest trading_bot/tests/` after every logic change.

### Coding Standard
- **Indentation**: 4-space, `snake_case` for functions, `PascalCase` for classes.
- **Type Hints**: Required for all function parameters and return types.
- **Logging**: Use `loguru.logger` exclusively.
- **I/O**: Use `async/await` for all data feed and monitoring operations.

---

## 6. Development & Operations Reference

### Build Commands
```bash
pip install -r requirements.txt
python main.py web         # Start Web Dashboard
python main.py phase4      # Start Live Trading (Console)
```

### FREE Data Feeds (No API Keys)
- **yfinance**: Stocks, Forex, and Crypto (via `data/yfinance_feed.py`).
- **CoinGecko**: Default crypto provider (via `data/coingecko_feed.py`).
- **ccxt**: Access to 30+ exchanges (via `data/ccxt_feed.py`).
