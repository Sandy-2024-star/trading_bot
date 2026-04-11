# MCP Servers for Trading Bot

## Overview

This document lists all MCP (Model Context Protocol) servers that can be integrated with the trading bot for enhanced capabilities.

## FREE MCP Servers

### 1. Filesystem MCP (Built-in)
**Status**: ✅ Available (no setup required)

Used by OpenCode/Cursor automatically for file operations.

### 2. PostgreSQL MCP
**Status**: ✅ Free (self-hosted)

```bash
# Install
npx -y @modelcontextprotocol/server-postgres

# Environment
export DATABASE_URL="postgresql://user:pass@localhost:5432/trading_bot"
```

**Use Case**: Query trade history, calculate win rates, analyze PnL

### 3. Tavily Search
**Status**: ✅ Freemium (1000 queries/month free)

```bash
# Install
npx -y @tavily/mcp-server

# Get API key at https://tavily.com
export TAVILY_API_KEY="your-api-key"
```

**Use Case**: 
- AI-powered news search
- Better sentiment analysis than NewsAPI
- Context-aware financial news

### 4. Exa Search
**Status**: ✅ Freemium (1000 queries/month free)

```bash
# Install
npx -y @exa/mcp-server

# Get API key at https://exa.ai
export EXA_API_KEY="your-api-key"
```

**Use Case**:
- Neural search for financial news
- Find articles by topic/company
- Research trading signals

### 5. GitHub MCP
**Status**: ✅ Free (with GitHub account)

```bash
# Install
npx -y @github/mcp-server

# Authenticate
export GITHUB_TOKEN="ghp_your_token"
```

**Use Case**:
- Track changes to trading strategies
- Manage trade logs in repo
- Version control for configs

## MCP Server Comparison

| Server | Cost | Rate Limit | Best For |
|--------|------|------------|----------|
| filesystem | FREE | Unlimited | File operations |
| postgres | FREE | Unlimited | Trade history queries |
| tavily | FREE | 1000/month | AI sentiment analysis |
| exa | FREE | 1000/month | Financial news search |
| github | FREE | GitHub limits | Version control |

## Setup Instructions

### Quick Setup

```bash
# 1. Install Node.js MCP servers
npx -y @modelcontextprotocol/server-postgres
npx -y @tavily/mcp-server
npx -y @exa/mcp-server
npx -y @github/mcp-server

# 2. Set environment variables
export TAVILY_API_KEY="tvly-..."
export EXA_API_KEY="..."
export GITHUB_TOKEN="ghp_..."

# 3. Add to OpenCode/Cursor MCP config
# See .mcp/mcp_config.json
```

### Verify Installation

```bash
# Test MCP server
npx -y @modelcontextprotocol/server-postgres --help
npx -y @tavily/mcp-server --help
```

## Usage Examples

### PostgreSQL MCP Queries

```
# "What was my win rate on BTC trades last week?"
SELECT symbol, COUNT(*) as trades, 
       SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins
FROM trades 
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY symbol;

# "Show my largest losing trades"
SELECT * FROM trades 
WHERE pnl < 0 
ORDER BY pnl ASC 
LIMIT 10;
```

### Tavily Search Examples

```
# "Find recent news about Fed rate decisions"
search(query="Federal Reserve interest rate decision 2026", max_results=5)

# "Get crypto sentiment for Bitcoin"
search(query="Bitcoin ETF approval news March 2026", max_results=10)
```

### Exa Search Examples

```
# "Research before trading gold"
search(query="MCX gold price prediction March 2026", num_results=10)

# "Find earnings reports"
search(query="Apple earnings report Q1 2026", category="finance")
```

## Integration with Trading Bot

The trading bot can use MCP servers via:

1. **Python API calls** - Direct API calls to Tavily/Exa
2. **AI Agent queries** - OpenCode/Cursor with MCP enabled
3. **Database queries** - PostgreSQL MCP for historical analysis

See `data/tavily_sentiment.py` and `data/yfinance_feed.py` for implementation.
