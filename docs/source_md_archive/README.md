# MT5 Bridge - Quick Setup

## One-Click Install (Mac/Linux)

```bash
cd mt5_third_parties
./install.sh
```

Done! The script will:
1. Check/install Docker
2. Build and start MT5 Bridge
3. Show your IP address for MT5 configuration

## Windows Setup

1. Double-click `install_ea.bat` to copy EA to MT5
2. Follow on-screen instructions

## Usage

```bash
# View logs
docker logs -f mt5-bridge

# Stop
docker compose down

# Restart
docker compose restart
```

## Files

```
mt5_third_parties/
├── install.sh          # One-click installer (Mac/Linux)
├── install_ea.bat      # EA installer (Windows)
├── docker-compose.yml   # Docker config
├── Dockerfile          # Container image
├── mql5/
│   └── Experts/
│       └── MT5SocketClient.mq5  # MT5 Expert Advisor
└── example.py          # Test script
```
