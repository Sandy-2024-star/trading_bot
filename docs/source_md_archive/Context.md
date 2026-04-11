# Automated Trading System — Project Context

## Goal
Build a multi-market automated trading system covering:
- Crypto (via CCXT - 30+ exchanges, FREE)
- Forex (via yfinance - Yahoo Finance, FREE)
- Indian markets (NSE/BSE via yfinance, FREE)
- Commodities (via yfinance, FREE)
- Global news sentiment (Tavily - 1000 free queries/month)

## Architecture (6 layers)
1. Data ingestion — market feeds + news APIs (yfinance, ccxt, Tavily)
2. Analysis engine — technical, fundamental, sentiment, correlation
3. Strategy layer — buy/sell signals, hedging, arbitrage
4. Risk management — position sizing, stop-loss, circuit breakers
5. Execution — broker APIs, order lifecycle, backtesting
6. Monitoring — PnL dashboard, alerts, Telegram notifications

## Phase plan
- Phase 1: ✅ COMPLETE - Data ingestion + signal engine
- Phase 2: ✅ COMPLETE - Strategy + risk engine
- Phase 3: ✅ COMPLETE - Broker API execution + backtesting
- Phase 4: ✅ COMPLETE - Monitoring dashboard + alerts

## 100% FREE Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPLETELY FREE STACK                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📊 MARKET DATA (No API Keys Required)                          │
│  ├── ✅ yfinance     → Stocks, ETFs, Forex, Crypto, Commodities │
│  ├── ✅ ccxt         → 30+ crypto exchanges (Binance, etc.)     │
│  └── ✅ CoinGecko    → Additional crypto data                    │
│                                                                  │
│  🔍 NEWS/SENTIMENT (Free Tiers)                                 │
│  ├── ✅ Tavily       → 1000 queries/month (AI-powered)           │
│  └── ✅ Exa Search   → Neural search for financial news         │
│                                                                  │
│  🏠 INFRASTRUCTURE (Self-Hosted)                                │
│  ├── ✅ SQLite       → Trade history (no server)                │
│  ├── ✅ PostgreSQL   → Advanced queries (self-hosted)            │
│  └── ✅ MCP servers  → AI agent integration                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Tools / APIs Available

### FREE Data Libraries (No API Keys)
- **yfinance**: Stock, ETF, Forex, Crypto data from Yahoo Finance
- **ccxt**: Multi-exchange crypto data (Binance, Coinbase, Kraken, etc.)

### FREE/Semi-Free APIs
- **Tavily Search**: AI-powered news (1000 free queries/month)
- **CoinGecko**: Crypto data (free tier)
- **Alpha Vantage**: 25 requests/day free

### MCP Servers (Free)
- **filesystem-mcp**: Built-in (OpenCode/Cursor)
- **postgres-mcp**: Trade history queries
- **tavily-mcp**: AI search for agents
- **exa-mcp**: Neural search for agents
- **github-mcp**: Version control

### Broker APIs (Require Account)
- [ ] Crypto.com MCP (already connected)
- [ ] OANDA or FXCM API (Forex)
- [ ] Zerodha Kite API (Indian markets)

## MCP Integration

See `MCP_SERVERS.md` for full documentation.

### Quick Setup
```bash
# Install MCP servers
npx -y @modelcontextprotocol/server-postgres
npx -y @tavily/mcp-server
npx -y @exa/mcp-server
npx -y @github/mcp-server

# Configure (already done)
# See trading_bot/.mcp/mcp_config.json

# Set environment variables
export TAVILY_API_KEY="tvly-..."
```

## Tech Stack
- **Language**: Python (primary)
- **Data**: yfinance, ccxt (FREE), SQLite, PostgreSQL
- **API Framework**: FastAPI
- **AI Integration**: MCP servers, Tavily, Local LLM support
- **Logging**: loguru

## Current Status
🎉 **PROJECT COMPLETE!** All 4 phases implemented with FREE data sources.

### Data Layer (Updated)
- ✅ **yfinance_feed.py**: FREE stocks/forex/crypto data
- ✅ **ccxt_feed.py**: FREE multi-exchange crypto data
- ✅ **tavily_sentiment.py**: AI-powered sentiment (1000 free qry/month)

### Previously Implemented
- ✅ **Strategy Layer**: Signal-based strategies, position/PnL tracking
- ✅ **Risk Management**: Position sizing, stop-loss/take-profit, circuit breakers
- ✅ **Execution**: Paper broker, order manager, backtesting engine
- ✅ **Monitoring**: PnL tracker, alerts, Telegram notifications

## Quick Start

```bash
cd trading_bot

# Install dependencies
pip install -r requirements.txt

# Run demos
python main.py              # Phase 1: Data + signals
python main.py phase2       # Phase 2: Strategy + risk
python main.py phase3       # Phase 3: Backtesting
python main.py phase4       # Phase 4: Live trading

# Test FREE data feeds
python -m data.yfinance_feed
python -m data.ccxt_feed
```

## Key Development Considerations

### General
- When building signal generators, implement common technical indicators: RSI, MACD, Bollinger Bands
- Use yfinance for stocks/forex, ccxt for multi-exchange crypto
- All broker API keys should be stored in `config/` directory (gitignored)

### FREE Data Sources
- **yfinance**: Best for stocks, ETFs, forex, and basic crypto
- **ccxt**: Best for advanced crypto trading across multiple exchanges
- **Tavily**: Best for AI-powered sentiment with full context

### Risk Management
- Risk management should be fail-safe: circuit breakers trigger before position limits
- Position sizing uses risk-based method by default (2% risk per trade)
- Circuit breaker automatically halts trading after 3 consecutive losses or 5% daily loss

---

## MT5 Integration (Optional)

MetaTrader 5 integration for trading Forex, Commodities, and Indices.

### Documentation
See `trading_bot/MT5_INTEGRATION.md` for full setup guide.

### Quick Setup
1. Create MetaApi account: https://app.metaapi.cloud
2. Connect MT5 terminal
3. Install: `pip install metaapi-python-sdk`
4. Configure METAAPI_TOKEN and METAAPI_ACCOUNT_ID in .env

### Benefits
- FREE tier: 500 transactions/month
- Cloud-based (no DLL needed)
- Trade Forex, Gold, Oil, Indices
