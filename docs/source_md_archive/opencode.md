# Agent Guidelines for Trading Bot

## Project Overview

Multi-market automated trading system trading across:
- Cryptocurrency (CCXT - 30+ exchanges, FREE)
- Forex (yfinance - Yahoo Finance, FREE)
- Indian markets (NSE/BSE via yfinance, FREE)
- Commodities (yfinance, FREE)
- News sentiment analysis (Tavily - 1000 free queries/month)

## 100% FREE Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPLETELY FREE STACK                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  🏠 INFRASTRUCTURE (Local/Self-Hosted)                          │
│  ├── ✅ filesystem-mcp      → Built-in (OpenCode, Cursor)       │
│  ├── ✅ github-mcp         → GitHub integration (free)          │
│  └── ✅ SQLite/PostgreSQL  → Trade history (self-hosted, $0)     │
│                                                                  │
│  📊 MARKET DATA (Python Libraries - No API Keys)                │
│  ├── ✅ yfinance           → Stocks, ETFs, Forex, Crypto        │
│  ├── ✅ ccxt               → 30+ crypto exchanges                │
│  └── ✅ CoinGecko          → Crypto data (free tier)            │
│                                                                  │
│  🔍 NEWS/SENTIMENT (Free Tiers)                                 │
│  ├── ✅ Tavily             → 1000 queries/month                 │
│  └── ✅ Exa Search         → Neural search (free tier)          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
trading_bot/
├── data/                # Market data fetchers
│   ├── yfinance_feed.py  # FREE - Stocks/Forex/Crypto (Yahoo Finance)
│   ├── ccxt_feed.py      # FREE - Multi-exchange crypto (30+ exchanges)
│   ├── tavily_sentiment.py  # FREE - AI sentiment (1000 qry/month)
│   ├── coingecko_feed.py # FREE - Crypto data
│   └── alpha_vantage_feed.py  # 25 req/day free
├── signals/             # Technical + sentiment analysis
├── strategy/             # Trading strategies
├── risk/                 # Position sizing, stop-loss, circuit breakers
├── execution/            # Brokers, order management, backtesting
├── monitoring/            # PnL tracking, alerts, dashboard
├── config/               # Environment-based configuration
├── tests/                # Unit tests
├── .mcp/                 # MCP server configuration
├── MCP_SERVERS.md        # MCP documentation
└── main.py               # Entry point
```

## Build, Run, and Test Commands

### Installation
```bash
cd trading_bot
pip install -r requirements.txt
cp config/settings.example.env config/.env

# Optional: Set free API keys
export TAVILY_API_KEY="tvly-..."    # 1000 free queries/month
```

### Running Phases
```bash
python main.py              # Phase 1: Data + signals demo
python main.py phase2       # Phase 2: Strategy + risk
python main.py phase3       # Phase 3: Backtesting
python main.py phase4       # Phase 4: Live trading (90s demo)
python main.py web          # Web dashboard
```

### Running Tests
```bash
# All tests
python -m pytest trading_bot/tests -v

# Single test file
python -m pytest trading_bot/tests/test_config.py -v

# Single test method
python -m pytest trading_bot/tests/test_config.py::ConfigValidationTests::test_known_sentiment_analyzer_is_valid -v
```

### Testing Free Data Feeds
```bash
# Test yfinance (Stocks/Forex/Crypto)
cd trading_bot && python -m data.yfinance_feed

# Test ccxt (Multi-exchange crypto)
cd trading_bot && python -m data.ccxt_feed

# Test Tavily sentiment
cd trading_bot && python -m data.tavily_sentiment
```

## MCP Server Setup

### Quick Setup
```bash
# 1. Install MCP servers
npx -y @modelcontextprotocol/server-postgres  # Trade history queries
npx -y @tavily/mcp-server                   # AI search
npx -y @exa/mcp-server                      # Neural search
npx -y @github/mcp-server                   # Version control

# 2. Configure (already done - see trading_bot/.mcp/mcp_config.json)
# 3. Set environment variables
export TAVILY_API_KEY="tvly-..."
export DATABASE_URL="postgresql://user:pass@localhost:5432/trading_bot"
```

### MCP Config Location
`trading_bot/.mcp/mcp_config.json`

## Code Style Guidelines

### Formatting
- 4-space indentation (no tabs)
- Maximum line length: 100 characters (soft)
- Single blank line between top-level definitions
- No trailing whitespace

### Naming Conventions
| Type | Convention | Example |
|------|------------|---------|
| Modules | snake_case | `paper_broker.py`, `position_sizer.py` |
| Classes | PascalCase | `PaperBroker`, `PositionSizer` |
| Functions/methods | snake_case | `calculate_size()`, `get_account_balance()` |
| Variables | snake_case | `account_balance`, `signal_strength` |
| Constants | UPPER_SNAKE_CASE | `MAX_POSITION_SIZE`, `RISK_PER_TRADE` |
| Enums | PascalCase + UPPER values | `SizingMethod.RISK_BASED` |

### Type Hints
- Use type hints for all function parameters and return types
- Use `Optional[Type]` for nullable types, not `Type | None`

```python
def calculate_size(
    account_balance: float,
    entry_price: float,
    stop_loss_price: Optional[float] = None
) -> float:
```

### Import Organization
Order imports by category with blank lines between:
1. Standard library imports
2. Third-party imports (yfinance, ccxt, pandas, loguru)
3. Local/application imports

```python
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import yfinance as yf
import ccxt
from loguru import logger

from execution.base_broker import BaseBroker, Order
```

## Testing Guidelines

### Test Structure
- Use `unittest` framework
- Mirror module names: `test_<module>.py`
- Class naming: `<Module>Tests`
- Method naming: `test_<behavior>_<expected_result>`

### Test Patterns
- Use `unittest.mock.patch` for external dependencies
- Restore original values in `finally` blocks
- Test both happy paths and failure cases

## Trading System Conventions

### Risk Management
- Risk-based position sizing is default (2% risk per trade)
- Stop loss is mandatory for risk-based sizing
- Circuit breaker halts trading after 3 consecutive losses or 5% daily loss

### Broker Interface
- All brokers inherit from `BaseBroker`
- Order lifecycle: PENDING → OPEN → FILLED/CANCELLED/REJECTED
- Paper broker uses 0.1% fee and 0.05% slippage by default

## Free Data Feed Comparison

| Library | Markets | Rate Limit | API Key Required |
|---------|---------|------------|-----------------|
| yfinance | Stocks, Forex, Crypto, Commodities | ~2000/day | NO |
| ccxt | 30+ crypto exchanges | Varies by exchange | NO (public data) |
| CoinGecko | Crypto only | 10-30/min | NO (free tier) |
| Tavily | News/Sentiment | 1000/month | YES (free tier) |

## Logging Convention
Use `loguru.logger` with appropriate levels:
- `logger.debug()` - Detailed debugging info
- `logger.info()` - Normal operation flow
- `logger.warning()` - Recoverable issues
- `logger.error()` - Operation failures

---

## MT5 Integration (Optional)

MetaTrader 5 integration enables trading Forex, Commodities, and Indices through MT5 accounts.

### Setup
1. Create MetaApi account: https://app.metaapi.cloud
2. Connect MT5 terminal to MetaApi
3. Install: `pip install metaapi-python-sdk`

### Configuration
```bash
# config/.env
METAAPI_TOKEN="your-token"
METAAPI_ACCOUNT_ID="your-account-id"
```

### Documentation
See `MT5_INTEGRATION.md` for full guide.

### Key Points
- FREE tier: 500 transactions/month
- No DLL required (cloud-based)
- Supports Forex, Commodities, Indices, Stocks
- Python SDK available
