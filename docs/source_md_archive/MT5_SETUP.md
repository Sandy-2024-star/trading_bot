# MT5 Setup Guide (Open-Source Bridge)

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  MT5_OPEN_SOURCE_BRIDGE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Your Mac                    Windows VM/Server                  │
│   ┌──────────────┐          ┌─────────────────┐                │
│   │              │  TCP/IP  │                 │               │
│   │  Python Bot  │ ◄───────►│    MT5 EA       │               │
│   │  (Server)   │  Port    │  MT5SocketClient │              │
│   │              │   1111   │                 │               │
│   └──────────────┘          └─────────────────┘                │
│         │                            │                          │
│         │                            │                          │
│         │                    ┌──────▼──────┐                   │
│         │                    │  MT5        │                   │
│         │                    │  Terminal   │                   │
│         │                    └─────────────┘                   │
│         │                                                    │
└─────────┴────────────────────────────────────────────────────┘
```

## Prerequisites

1. **MetaTrader 5** installed on Windows (VM or dedicated server)
2. **MT5 Demo Account** (already have: Sandesh P, Server: MetaQuotes-Demo)
3. **Docker** installed on your Mac

## Setup Steps

### Step 1: Start MT5 Bridge via Docker

```bash
cd mt5_third_parties
./setup_docker.sh
```

Or manually:
```bash
cd mt5_third_parties
docker compose up -d
docker compose logs -f  # Watch logs
```

### Step 2: Get MT5 EA (Expert Advisor)

The EA file is in `../mt5_third_parties/mql5/Experts/MT5SocketClient.mq5`

Copy this file to your Windows MT5:
1. Open File Explorer
2. Navigate to MT5 data folder (usually `C:\Users\<YourName>\AppData\Roaming\MetaQuotes\Terminal\<RandomID>\MQL5\Experts\`)
3. Copy `MT5SocketClient.mq5` there
4. Open MetaEditor in MT5
5. Compile the EA (F7 or right-click → Compile)

### Step 3: Configure MT5

1. Open MT5
2. Go to **Tools** → **Options** → **Expert Advisors**
3. Check **"Allow WebRequest for listed URL"**
4. Add your Mac's IP address (e.g., `192.168.1.100`)
5. Click OK

### Step 4: Get Your Mac's IP Address

```bash
# On Mac
ipconfig getifaddr en0
# or
ifconfig | grep "inet "
```

### Step 5: Attach EA to Chart

1. In MT5, open any chart (e.g., EURUSD)
2. In Navigator → Expert Advisors, drag **MT5SocketClient** to chart
3. Configure inputs:
   - `ServerAddress`: Your Mac's IP address (e.g., `192.168.1.100`)
   - `ServerPort`: `1111`
4. Enable "Allow live trading" if you want to trade

### Step 6: Verify Docker Container is Running

```bash
docker ps | grep mt5-bridge
```

You should see:
```
CONTAINER ID   IMAGE           STATUS
abc123def456   mt5_third_parties-mt5-bridge   Up 2 minutes
```

Check logs for connection:
```bash
docker compose -f mt5_third_parties/docker-compose.yml logs -f
```

When MT5 EA connects, you'll see:
```
MT5 EA connected from ('192.168.x.x', xxxxx)
```

## Alternative: Use VPS

If you don't want to run Windows VM all the time:

1. Rent a Windows VPS (e.g., Contabo, AWS Windows, DigitalOcean Windows)
2. Install MT5 on the VPS
3. Configure EA to connect to your Python server
4. Your Python bot runs on your Mac, VPS handles MT5

## Connection Options

| Setup | Pros | Cons |
|-------|------|------|
| Windows VM on Mac | Free (with existing VM) | VM must be running |
| Dedicated Windows PC | Always on | Hardware cost |
| Windows VPS | Always on, no local VM | Monthly cost (~$10-20) |

## Files Location

```
Market/
├── trading_bot/
│   ├── data/mt5_feed.py      # MT5 data feed (using mt5_bridge)
│   ├── execution/mt5_broker.py # MT5 broker (using mt5_bridge)
│   └── ...
└── mt5_third_parties/         # Open-source MT5 bridge
    ├── mt5_bridge/           # Python package
    ├── mql5/                 # MT5 EA files
    └── example.py            # Usage example
```

## Quick Test

```bash
# Terminal 1: Start Python server
cd mt5_third_parties
python -m mt5_bridge.main --port 1111

# Terminal 2: Run example
cd mt5_third_parties
python example.py
```

## Troubleshooting

**EA can't connect:**
- Check firewall allows port 1111
- Verify IP address in EA settings
- Ensure "Allow WebRequest" is enabled

**Orders fail:**
- Check symbol name matches broker (e.g., "EURUSD" not "EURUSDm")
- Verify sufficient margin
- Check market is open

**Connection drops:**
- Use a stable network
- Consider VPS for 24/7 operation
