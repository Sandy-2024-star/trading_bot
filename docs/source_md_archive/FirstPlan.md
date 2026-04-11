# MT5-Python Socket Bridge

Create a Client-Server socket bridge between Python (Server) and MetaTrader 5 (Client/EA).

> **Note**: Python runs on Linux host, MT5 runs on Windows VM. Socket communication enables cross-platform integration.

## System Architecture

```
+------------------+          TCP/IP          +------------------+
|  Python Server   | <----------------------> |   MT5 EA Client  |
|  (Linux Host)    |      Port 1111           |  (Windows VM)    |
+------------------+                          +------------------+
```

**Important**: MQL5 only supports client-side sockets (`SocketCreate`, `SocketConnect`). It does NOT have `SocketListen` or `SocketAccept`. Therefore:
- **Python = TCP Server** (listens for connections)
- **MT5 EA = TCP Client** (connects to Python)

---

## 1. MT5 EA Client (MQL5)

### Input Parameters
| Parameter | Default | Description |
|-----------|---------|-------------|
| ServerAddress | "192.168.x.x" | Python server IP |
| ServerPort | 1111 | TCP port |
| ReconnectDelayMs | 5000 | Reconnect delay |

### Connection Lifecycle
1. `OnInit()`: `SocketCreate()` + `SocketConnect()`
2. `OnTimer()`: Poll commands, send heartbeat
3. `OnDeinit()`: Graceful disconnect

### MT5 Configuration
Tools > Options > Expert Advisors > Allow WebRequest for: `192.168.x.x`

---

## 2. Python Server

### Core Functions
- TCP Server on port 1111
- Accept MT5 connections
- Send commands, parse responses

### API Interface
```python
class MT5Bridge:
    async def buy(symbol, volume, sl=None, tp=None) -> OrderResult
    async def sell(symbol, volume, sl=None, tp=None) -> OrderResult
    async def get_rates(symbol, timeframe, count) -> DataFrame
    async def get_tick(symbol) -> TickData
    async def get_account() -> AccountInfo
    async def get_positions() -> List[Position]
    async def close_position(ticket) -> CloseResult
```

---

## 3. Message Protocol

**Format**: JSON with newline terminator (`\n`)

### Request (Python → MT5)
```json
{"id": "uuid", "action": "TRADE", "params": {...}}
```

### Response (MT5 → Python)
```json
{"id": "uuid", "success": true, "error_code": 0, "data": {...}}
```

---

## 4. Commands

| Action | Params | Response Data |
|--------|--------|---------------|
| TRADE | symbol, type, volume, sl, tp | ticket, price_executed |
| GET_DATA | symbol, timeframe, count | rates[] |
| GET_TICK | symbol | bid, ask, time |
| GET_ACCOUNT | - | balance, equity, margin |
| GET_POSITIONS | - | positions[] |
| CLOSE_POSITION | ticket | close_price, profit |
| HEARTBEAT | - | timestamp |

### Order Types
BUY, SELL, BUY_LIMIT, SELL_LIMIT, BUY_STOP, SELL_STOP

### Timeframes
M1, M5, M15, M30, H1, H4, D1, W1, MN1

---

## 5. Project Structure

```
mt5_python_bridge/
├── mql5/
│   └── MT5SocketClient.mq5
├── python/
│   ├── mt5_server.py
│   ├── mt5_bridge.py
│   └── models.py
└── tests/
```

---

## 6. Implementation Order

1. Python TCP server (listen for connections)
2. MT5 EA socket client (connect to Python)
3. Heartbeat mechanism
4. TRADE command
5. GET_DATA command
6. Remaining commands
7. Error handling + reconnection
8. Tests
