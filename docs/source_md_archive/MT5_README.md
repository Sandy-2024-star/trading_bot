# MT5 Integration - Start Here

## Quick Summary

Integrate MetaTrader 5 (MT5) into your trading bot for **Forex, Gold, Oil, and Indices** trading using the open-source `mt5_bridge`.

## Setup Method: Docker (Recommended)

```bash
cd mt5_third_parties
./setup_docker.sh
```

## Documentation Guide

| Document | Purpose | Read First? |
|----------|---------|-------------|
| `MT5_SETUP_QUICKREF.md` | 5-minute setup guide | YES |
| `MT5_ANALYSIS.md` | Project analysis, what to reuse | YES |
| `MT5_INTEGRATION.md` | Full integration guide | Reference |
| `MT5_IMPLEMENTATION_PLAN.md` | Step-by-step code plan | Reference |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Your Mac                    Windows VM/Server          │
│  ┌──────────────┐          ┌─────────────────┐         │
│  │ Docker       │  TCP/IP  │                 │         │
│  │ mt5_bridge   │◄────────►│  MT5 EA Client  │         │
│  │ (Python 3.11)│  1111    │  MT5SocketClient│         │
│  └──────────────┘          └─────────────────┘         │
└─────────────────────────────────────────────────────────┘
```

## What You Need

1. **Docker** installed on Mac
2. **MT5 Platform** installed on Windows (VM or dedicated)
3. **MT5 Demo Account**: Sandesh P, Server: MetaQuotes-Demo

## Quick Setup Steps

1. **Start Docker bridge**:
   ```bash
   cd mt5_third_parties
   docker compose up -d
   ```

2. **Install MT5 EA on Windows**:
   - Copy `mql5/Experts/MT5SocketClient.mq5` to MT5's MQL5/Experts folder
   - Compile in MetaEditor

3. **Configure MT5**:
   - Tools → Options → Expert Advisors
   - Enable "Allow WebRequest for listed URL"
   - Add: `http://<your-mac-ip>:1111`

4. **Attach EA to chart**:
   - ServerAddress: Your Mac's IP
   - ServerPort: 1111

## Files Created

| File | Purpose |
|------|---------|
| `data/mt5_feed.py` | MT5 market data feed |
| `execution/mt5_broker.py` | MT5 broker adapter |
| `mt5_third_parties/Dockerfile` | Docker image for mt5_bridge |
| `mt5_third_parties/docker-compose.yml` | Docker Compose setup |

## Ready to Implement?

1. Read `MT5_SETUP_QUICKREF.md`
2. Start Docker: `cd mt5_third_parties && docker compose up -d`
3. Tell me to implement → I'll create the code
