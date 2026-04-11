# Docker Deployment Guide 🚀

This guide explains how to deploy the entire trading bot system (Bot, Redis, PostgreSQL) using Docker.

## 📋 Prerequisites
- Docker installed on your machine/VPS.
- Docker Compose installed.

## 🚀 Quick Start (One-Click Deployment)

1.  **Configure Environment**: 
    Ensure `trading_bot/config/.env` is populated with your API keys.
    *Note: Docker Compose will automatically map this file into the container.*

2.  **Build and Start**:
    ```bash
    docker-compose up --build -d
    ```
    *The `-d` flag runs the containers in the background.*

3.  **Verify**:
    Open your browser and navigate to `http://localhost:8000` to access the dashboard.

## 🛠 Useful Commands

### Check Logs
To see what the bot is doing in real-time:
```bash
docker logs -f trading_bot
```

### Stop the System
```bash
docker-compose down
```

### Restart Only the Bot
If you made code changes and want to rebuild only the bot:
```bash
docker-compose up --build -d bot
```

### Access Database
To enter the PostgreSQL terminal inside the container:
```bash
docker exec -it trading_bot_postgres psql -U postgres -d trading_bot
```

## 💾 Persistence
- **Trade History**: Stored in a Docker volume `postgres_data`.
- **AI Models**: Stored in your local `./data/models` directory.
- **Config**: Your local `./trading_bot/config/.env` is synced with the container.

---
*Note: The bot is configured to run the Web Dashboard by default in Docker. If you wish to run a specific phase, modify the `command:` section in `docker-compose.yml`.*
