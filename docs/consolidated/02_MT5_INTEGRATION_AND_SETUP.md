# 02 MT5 Integration & Setup Guide

## 1. Overview & Strategy

The MetaTrader 5 (MT5) integration enables the trading bot to access **Forex, Commodities, Indices, and Global Stocks** using institutional-grade execution. The system is designed to keep strategy decisions within the Python bot while using MT5 as the execution and visualization layer.

### Core Objectives
*   **Decoupled Execution**: Python decides, MT5 executes.
*   **Multi-Market Support**: Access Forex (EURUSD, USDINR), Commodities (Gold, Oil), and Indices (US100, Nifty 50).
*   **Visual Validation**: Use MT5 charts to visualize bot decisions, entries, and exits.
*   **Modular Architecture**: Plug-and-play integration using the existing `BaseBroker` and `MarketDataFeed` interfaces.

---

## 2. Architecture & Integration Options

There are three primary ways to integrate MT5. Choose the one that fits your deployment environment:

| Feature | MetaApi Cloud | Open Source Bridge | Direct MT5 Library |
| :--- | :--- | :--- | :--- |
| **Best For** | Cloud/VPS, No Windows VM | Mac users with Windows VM | Windows-native bot |
| **Connectivity** | REST/WebSocket (Cloud) | TCP/IP Socket (Local/LAN) | Direct Python DLL (Local) |
| **Cost** | Free tier (500 tx/mo) | Free (Open Source) | Free |
| **Complexity** | Low (API-based) | Medium (Socket/Docker) | Low (Windows only) |
| **Architecture** | Bot -> MetaApi -> MT5 | Bot -> Bridge -> EA | Bot -> MT5 Library |

### Preferred Architectures

#### A. Open Source Bridge (Mac/Linux Host + Windows VM)
```
┌──────────────────────────┐          TCP/IP          ┌──────────────────────────┐
│  Mac/Linux Host          │  Port 1111 (Socket)      │  Windows VM / Server     │
│  ┌────────────────────┐  │ <─────────────────────>  │  ┌────────────────────┐  │
│  │ Python Trading Bot │  │                          │  │ MetaTrader 5       │  │
│  │ (TCP Server)       │  │                          │  │ (Socket Client EA) │  │
│  └────────────────────┘  │                          │  └────────────────────┘  │
└──────────────────────────┘                          └──────────────────────────┘
```

#### B. MetaApi Cloud (Cloud-Native)
```
┌──────────────┐      ┌──────────┐       ┌───────────┐
│ Trading Bot  │ ───> │ MetaApi  │ ───>  │ MT5       │
│ (Python SDK) │ <─── │ Cloud    │ <───  │ Terminal  │
└──────────────┘      └──────────┘       └───────────┘
```

---

## 3. Setup Guide: Open Source Socket Bridge (Recommended)

This method uses a Docker-based bridge on your host (Mac) and a custom Expert Advisor (EA) in your MT5 terminal (Windows).

### Step 1: Start the Bridge (Mac)
```bash
cd mt5_third_parties
./install.sh  # Builds and starts Docker container
```
Alternatively, use manual docker commands:
```bash
docker compose -f mt5_third_parties/docker-compose.yml up -d
```

### Step 2: Install EA in MT5 (Windows)
1.  Locate `mt5_third_parties/mql5/Experts/MT5SocketClient.mq5`.
2.  In MT5, go to `File` -> `Open Data Folder`.
3.  Navigate to `MQL5/Experts/` and copy the `.mq5` file there.
4.  Open **MetaEditor** (`F4`), right-click the file, and select **Compile**.

### Step 3: Configure MT5 Connection
1.  **Enable WebRequest**: `Tools` -> `Options` -> `Expert Advisors`.
2.  Check "Allow WebRequest for listed URL" and add your Mac's IP (e.g., `http://192.168.1.10:1111`).
3.  **Attach EA**: Drag `MT5SocketClient` to any chart.
4.  **Inputs**:
    *   `ServerAddress`: Your Mac's IP.
    *   `ServerPort`: `1111`.
5.  **Enable Live Trading**: Ensure "Allow live trading" is checked in the EA properties.

---

## 4. Setup Guide: MetaApi Cloud (Alternative)

### Step 1: Create Credentials
1.  Sign up at [metaapi.cloud](https://app.metaapi.cloud).
2.  Create a "MetaTrader broker server" account and enter your broker details.
3.  Copy your **API Token** and **Account ID**.

### Step 2: Configure Bot
Add to your `config/.env`:
```bash
METAAPI_TOKEN="your-token"
METAAPI_ACCOUNT_ID="your-account-id"
```

---

## 5. Implementation Roadmap

### Phase 1: Environment & Config
1.  **Dependencies**: Add `metaapi-python-sdk` or `MetaTrader5` (if Windows) to `requirements.txt`.
2.  **Config**: Update `config/config.py` to load MT5 credentials.

### Phase 2: Create MT5 Components
1.  **MT5 Data Feed** (`data/mt5_feed.py`):
    *   Inherit from `MarketDataFeed`.
    *   Implement `get_candlesticks` and `get_ticker`.
2.  **MT5 Broker** (`execution/mt5_broker.py`):
    *   Inherit from `BaseBroker`.
    *   Implement `place_order`, `cancel_order`, `get_account_balance`, and `get_position`.

### Phase 3: Update Factory & Registry
1.  **Factory**: Update `data/factory.py` and create `execution/broker_factory.py` to instantiate MT5 components based on config.
2.  **Registry**: Update `data/market_registry.py` to route Forex and Commodity symbols to the MT5 feed.

### Phase 4: Integration & Testing
1.  **Main Entry**: Add `demo_mt5()` phase to `main.py`.
2.  **Test Suite**: Create `tests/test_mt5_integration.py` to verify connection and order lifecycle.

---

## 6. Technical Reference

### File Organization (Reuse Strategy)

| Component | Status | Action |
| :--- | :--- | :--- |
| `execution/base_broker.py` | ✅ Reuse | Inherit `BaseBroker` for `MT5Broker`. |
| `execution/paper_broker.py`| ✅ Reference | Use as template for order lifecycle. |
| `execution/order_manager.py`| ✅ Reuse | Works out-of-the-box with `MT5Broker`. |
| `data/base_feed.py` | ✅ Reuse | Inherit `MarketDataFeed` for `MT5Feed`. |
| `data/factory.py` | 🔄 Update | Add MT5 provider selection. |

### Symbol Mapping
The bot uses standardized symbols which must be mapped to broker-specific names in MT5:

| Bot Symbol | MT5 Common Name | Market |
| :--- | :--- | :--- |
| EURUSD | EURUSD / EURUSD.m | Forex |
| XAUUSD | GOLD / XAUUSD | Commodity |
| US100 | NAS100 / US100 | Index |
| BTCUSD | BTCUSD / Bitcoin | Crypto |

### Example: Basic Connection (MetaApi)
```python
from metaapi_cloud_sdk import MetaApi

async def test_mt5():
    api = MetaApi(token="YOUR_TOKEN")
    account = await api.metatrader_account_api.get_account("ACCOUNT_ID")
    await account.connect()
    print(f"Balance: {account.balance}")
```

---

## 7. Troubleshooting

### Connection Issues
*   **EA Red Face**: Check "Allow WebRequest" settings and firewall on port 1111.
*   **Invalid Symbol**: Ensure the symbol is active in MT5's "Market Watch".
*   **Insufficient Margin**: Check account balance and lot size (MT5 lots differ from Crypto).

### Best Practices
1.  **Always Use SL/TP**: Never send an order without a Stop Loss.
2.  **Heartbeat Monitoring**: Use the socket bridge heartbeat to detect disconnections.
3.  **Demo First**: Always test with a demo account before live trading.
4.  **Rate Limiting**: Cache prices locally to stay within MetaApi transaction limits.

---
**Document Version**: 3.0 (2026-04-01)
**Status**: Consolidated from MT5 Integration Suite
