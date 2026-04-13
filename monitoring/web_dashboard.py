"""
Web dashboard for trading bot monitoring.
Provides real-time web interface with light/dark/system themes.
"""

import asyncio
from datetime import datetime
from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    BackgroundTasks,
    HTTPException,
    status,
    Depends,
)
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Any
from loguru import logger
from fastapi.security import OAuth2PasswordRequestForm

from monitoring.dashboard_data import DashboardData
from monitoring.auth import (
    create_access_token,
    get_current_user,
    authenticate_user,
    oauth2_scheme,
)


class WebDashboard:
    """
    Web-based dashboard using FastAPI.

    Features:
    - Real-time updates via polling or WebSocket
    - Light/Dark/System theme support
    - Responsive design
    - Auto-refresh
    """

    def __init__(
        self, dashboard_data: DashboardData, host: str = "0.0.0.0", port: int = 8000
    ):
        self.dashboard_data = dashboard_data
        self.host = host
        self.port = port
        self.app = FastAPI(title="Trading Bot Dashboard")
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self.active_connections: List[WebSocket] = []

        self._setup_routes()
        logger.info(f"WebDashboard initialized on {host}:{port}")

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected WebSocket clients."""
        if not self.active_connections:
            return

        json_data = self._serialize_for_json(message)
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(json_data)
            except Exception:
                disconnected.append(connection)

        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)

    def _serialize_for_json(self, value):
        """Recursively serialize datetime values for JSON responses."""
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, dict):
            return {key: self._serialize_for_json(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._serialize_for_json(item) for item in value]
        return value

    def _setup_routes(self):
        """Setup FastAPI routes."""

        @self.app.get("/", response_class=HTMLResponse)
        async def get_dashboard():
            """Serve the main dashboard HTML."""
            return self._get_dashboard_html()

        @self.app.post("/api/login")
        async def login(form_data: OAuth2PasswordRequestForm = Depends()):
            """Authenticate user and return JWT."""
            if not authenticate_user(form_data.username, form_data.password):
                raise HTTPException(
                    status_code=401, detail="Incorrect username or password"
                )

            access_token = create_access_token(data={"sub": form_data.username})
            return {"access_token": access_token, "token_type": "bearer"}

        @self.app.get("/api/dashboard")
        async def get_dashboard_data(user: str = Depends(get_current_user)):
            """Get dashboard data as JSON."""
            data = self.dashboard_data.get_full_dashboard()
            return self._serialize_for_json(data)

        @self.app.get("/api/candles/{symbol}")
        async def get_candles(
            symbol: str,
            timeframe: str = "1h",
            limit: int = 100,
            user: str = Depends(get_current_user),
        ):
            """Get historical candles for a specific symbol."""
            try:
                import yfinance as yf
                import pandas as pd
                import asyncio

                # Map symbol to yfinance format
                mapping = {
                    "BTCUSD": "BTC-USD",
                    "ETHUSD": "ETH-USD",
                    "GOLD": "GC=F",
                    "BTC-USD": "BTC-USD",
                }
                yf_symbol = mapping.get(symbol, symbol)
                logger.info(f"Mapping {symbol} -> {yf_symbol}")

                interval_map = {"1m": "1m", "5m": "5m", "1h": "1h", "1D": "1d"}
                interval = interval_map.get(timeframe, "1h")
                period = "5d" if interval == "1h" else "1d"

                # Run in executor to avoid blocking
                loop = asyncio.get_event_loop()
                df = await loop.run_in_executor(
                    None,
                    lambda: yf.download(
                        yf_symbol, period=period, interval=interval, progress=False
                    ),
                )

                if df.empty:
                    logger.warning(f"No data from yfinance for {yf_symbol}")
                    return []

                # Handle MultiIndex columns properly
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = pd.Index([c[0].lower() for c in df.columns])

                df = df.reset_index()
                df.columns = [c.lower() for c in df.columns]

                # Format output
                candles = []
                for _, row in df.tail(limit).iterrows():
                    ts = row["datetime"] if "datetime" in row else row["date"]
                    candles.append(
                        {
                            "time": int(ts.timestamp()),
                            "open": float(row["open"]),
                            "high": float(row["high"]),
                            "low": float(row["low"]),
                            "close": float(row["close"]),
                            "volume": float(row.get("volume", 0)),
                        }
                    )

                logger.info(f"Returning {len(candles)} candles for {symbol}")
                return candles
            except Exception as e:
                logger.error(f"Error fetching candles for {symbol}: {e}")
                return {"error": str(e)}

        @self.app.get("/api/params")
        async def get_params(user: str = Depends(get_current_user)):
            """Get currently tuned symbol parameters."""
            from strategy.factory import load_symbol_params

            return load_symbol_params()

        @self.app.put("/api/params")
        async def update_params(
            new_params: dict, user: str = Depends(get_current_user)
        ):
            """Update tuned symbol parameters and save to disk."""
            import json
            import os

            try:
                config_dir = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "config",
                )
                params_file = os.path.join(config_dir, "symbol_params.json")

                with open(params_file, "w") as f:
                    json.dump(new_params, f, indent=4)

                # Notify the strategy if it's currently active in LiveTrader
                if self.dashboard_data.trader and self.dashboard_data.trader.strategy:
                    self.dashboard_data.trader.strategy.symbol_params = new_params
                    logger.info("Live strategy parameters updated from dashboard")

                return {
                    "status": "success",
                    "message": "Parameters updated successfully",
                }
            except Exception as e:
                logger.error(f"Error saving parameters: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/tune/{symbol}")
        async def trigger_tuning(
            symbol: str,
            background_tasks: BackgroundTasks,
            user: str = Depends(get_current_user),
        ):
            """Trigger automated strategy tuning for a symbol."""
            from RND.experiments.tune_strategy import tune_symbol

            background_tasks.add_task(tune_symbol, symbol)
            return {"status": "Tuning started in background", "symbol": symbol}

        @self.app.post("/api/bot/pause")
        async def pause_bot(user: str = Depends(get_current_user)):
            """Pause the trading bot."""
            if self.dashboard_data.trader:
                self.dashboard_data.trader.paused = True
                logger.info("Bot PAUSED via dashboard")
                await self.broadcast(self.dashboard_data.get_full_dashboard())
                return {"status": "paused"}
            return {"error": "Trader not initialized"}

        @self.app.post("/api/bot/resume")
        async def resume_bot(user: str = Depends(get_current_user)):
            """Resume the trading bot."""
            if self.dashboard_data.trader:
                self.dashboard_data.trader.paused = False
                logger.info("Bot RESUMED via dashboard")
                await self.broadcast(self.dashboard_data.get_full_dashboard())
                return {"status": "running"}
            return {"error": "Trader not initialized"}

        @self.app.get("/api/correlation")
        async def get_correlation(user: str = Depends(get_current_user)):
            """Get the current symbol correlation matrix."""
            if (
                self.dashboard_data.trader
                and self.dashboard_data.trader.correlation_engine
            ):
                return self.dashboard_data.trader.correlation_engine.get_matrix_dict()
            return {}

        @self.app.post("/api/positions/close/{symbol}")
        async def close_position(symbol: str, user: str = Depends(get_current_user)):
            """Manually close a position."""
            if self.dashboard_data.trader and self.dashboard_data.trader.order_manager:
                positions = self.dashboard_data.trader.strategy.get_open_positions(
                    symbol
                )
                if positions:
                    price = await self.dashboard_data.trader.broker.get_current_price(
                        symbol
                    )
                    await self.dashboard_data.trader.order_manager.close_position(
                        positions[0], price
                    )
                    logger.info(f"Position {symbol} CLOSED manually via dashboard")
                    await self.broadcast(self.dashboard_data.get_full_dashboard())
                    return {"status": "closed", "symbol": symbol}
                return {"error": f"No open position found for {symbol}"}
            return {"error": "Trader/OrderManager not initialized"}

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            # Get token from subprotocol (standard way to pass token to WebSocket)
            token = None
            if "Sec-WebSocket-Protocol" in websocket.headers:
                protocols = websocket.headers["Sec-WebSocket-Protocol"].split(",")
                for p in protocols:
                    if p.strip().startswith("bearer."):
                        token = p.strip().replace("bearer.", "")
                        break

            await websocket.accept(subprotocol=f"bearer.{token}" if token else None)

            # Verify token
            try:
                await get_current_user(token)
            except Exception:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return

            self.active_connections.append(websocket)
            try:
                # Send initial data immediately
                initial_data = self.dashboard_data.get_full_dashboard()
                await websocket.send_json(self._serialize_for_json(initial_data))

                while True:
                    # Connection stays open to receive broadcasts from other components
                    await websocket.receive_text()
            except WebSocketDisconnect:
                if websocket in self.active_connections:
                    self.active_connections.remove(websocket)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                if websocket in self.active_connections:
                    self.active_connections.remove(websocket)

    def _get_dashboard_html(self) -> str:
        """Generate dashboard HTML with embedded CSS and JS."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading Bot Dashboard</title>
    <script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --bg-primary: #ffffff;
            --bg-secondary: #f5f5f5;
            --bg-card: #ffffff;
            --text-primary: #1a1a1a;
            --text-secondary: #666666;
            --border: #e0e0e0;
            --accent: #2196F3;
            --success: #4CAF50;
            --danger: #f44336;
            --warning: #ff9800;
            --shadow: rgba(0, 0, 0, 0.1);
        }

        [data-theme="dark"] {
            --bg-primary: #0a0c10;
            --bg-secondary: #111318;
            --bg-card: #16191f;
            --text-primary: #e8eaf0;
            --text-secondary: #9ca3af;
            --border: #22262e;
            --accent: #00e5ff;
            --success: #00ff88;
            --danger: #ff3b5c;
            --warning: #ffd700;
            --shadow: rgba(0, 0, 0, 0.3);
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background:
                radial-gradient(circle at top left, rgba(33, 150, 243, 0.09), transparent 55%),
                radial-gradient(circle at bottom right, rgba(0, 229, 255, 0.07), transparent 55%),
                var(--bg-primary);
            color: var(--text-primary);
            transition: background 0.3s, color 0.3s;
        }

        .header {
            background: var(--bg-card);
            border-bottom: 1px solid var(--border);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 4px var(--shadow);
        }

        .header h1 {
            font-size: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.3rem;
            background: var(--success);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            background: white;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .theme-switcher {
            display: flex;
            gap: 0.5rem;
            background: var(--bg-secondary);
            padding: 0.25rem;
            border-radius: 8px;
        }

        .theme-btn {
            background: none;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            cursor: pointer;
            color: var(--text-secondary);
            font-size: 0.9rem;
            transition: all 0.2s;
        }

        .theme-btn:hover {
            background: var(--bg-card);
            color: var(--text-primary);
        }

        .theme-btn.active {
            background: var(--accent);
            color: white;
        }

        .container {
            max-width: 1440px;
            margin: 0 auto;
            padding: 2rem;
        }

        .system-bar {
            max-width: 1440px;
            margin: 1rem auto 0;
            padding: 0.75rem 2rem;
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 1rem;
            background: rgba(15, 118, 255, 0.05);
            border-top: 1px solid var(--border);
            border-bottom: 1px solid var(--border);
            backdrop-filter: blur(10px);
        }

        .system-pill {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.8rem;
            color: var(--text-secondary);
            min-width: 0;
        }

        .system-pill-label {
            font-weight: 600;
            color: var(--text-primary);
        }

        .system-pill-dot {
            width: 6px;
            height: 6px;
            border-radius: 999px;
            background: var(--success);
        }

        .system-pill-dot.danger {
            background: var(--danger);
        }

        .tab-bar {
            display: inline-flex;
            gap: 0.5rem;
            background: var(--bg-secondary);
            padding: 0.35rem;
            border-radius: 999px;
            margin-bottom: 1.5rem;
        }

        .tab-btn {
            background: transparent;
            border: none;
            color: var(--text-secondary);
            padding: 0.75rem 1.1rem;
            border-radius: 999px;
            cursor: pointer;
            font-size: 0.95rem;
            font-weight: 600;
            transition: all 0.2s ease;
        }

        .tab-btn:hover {
            color: var(--text-primary);
            background: var(--bg-card);
        }

        .tab-btn.active {
            background: var(--accent);
            color: white;
        }

        .tab-panel {
            display: none;
        }

        .tab-panel.active {
            display: block;
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }

        .metric-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 8px var(--shadow);
            transition: transform 0.2s;
        }

        .metric-card:hover {
            transform: translateY(-2px);
        }

        .metric-label {
            color: var(--text-secondary);
            font-size: 0.875rem;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .metric-value {
            font-size: 1.75rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }

        .metric-change {
            font-size: 0.875rem;
            font-weight: 600;
        }

        .positive { color: var(--success); }
        .negative { color: var(--danger); }

        .section {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 8px var(--shadow);
        }

        .section-header {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th {
            text-align: left;
            padding: 0.75rem;
            border-bottom: 2px solid var(--border);
            color: var(--text-secondary);
            font-weight: 600;
            font-size: 0.875rem;
        }

        td {
            padding: 0.75rem;
            border-bottom: 1px solid var(--border);
        }

        tr:last-child td {
            border-bottom: none;
        }

        .badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .badge-success { background: var(--success); color: white; }
        .badge-danger { background: var(--danger); color: white; }
        .badge-warning { background: var(--warning); color: white; }
        .badge-info { background: var(--accent); color: white; }

        .alert-item {
            padding: 0.75rem;
            border-left: 3px solid var(--accent);
            background: var(--bg-secondary);
            margin-bottom: 0.5rem;
            border-radius: 4px;
            font-size: 0.875rem;
        }

        .alert-time {
            color: var(--text-secondary);
            font-size: 0.75rem;
            margin-right: 0.5rem;
        }

        .empty-state {
            text-align: center;
            padding: 2rem;
            color: var(--text-secondary);
        }

        /* Login Screen */
        #login-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: var(--bg-primary);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }

        .login-card {
            background: var(--bg-card);
            padding: 2.5rem;
            border-radius: 16px;
            box-shadow: 0 8px 32px var(--shadow);
            width: 100%;
            max-width: 400px;
            border: 1px solid var(--border);
        }

        .login-card h2 {
            margin-bottom: 1.5rem;
            text-align: center;
        }

        .form-group {
            margin-bottom: 1.25rem;
        }

        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-size: 0.875rem;
            font-weight: 600;
        }

        .form-group input {
            width: 100%;
            padding: 0.75rem;
            border-radius: 8px;
            border: 1px solid var(--border);
            background: var(--bg-secondary);
            color: var(--text-primary);
        }

        .login-btn {
            width: 100%;
            padding: 0.75rem;
            background: var(--accent);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 1rem;
        }

        .login-error {
            color: var(--danger);
            font-size: 0.875rem;
            margin-top: 1rem;
            text-align: center;
            display: none;
        }

        @media (max-width: 768px) {
            .container {
                padding: 1rem;
            }

            .system-bar {
                padding: 0.75rem 1rem;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                row-gap: 0.75rem;
            }

            .header {
                flex-direction: column;
                gap: 1rem;
            }

            .metrics-grid {
                grid-template-columns: 1fr;
            }

            table {
                font-size: 0.875rem;
            }
        }
    </style>
</head>
<body>
    <div id="login-overlay">
        <div class="login-card">
            <h2>🔐 Dashboard Login</h2>
            <form id="login-form">
                <div class="form-group">
                    <label for="username">Username</label>
                    <input type="text" id="username" required autocomplete="username">
                </div>
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" required autocomplete="current-password">
                </div>
                <button type="submit" class="login-btn">Login</button>
                <div id="login-error" class="login-error">Invalid username or password</div>
            </form>
        </div>
    </div>

    <div class="header">
        <h1>
            🤖 Trading Bot Dashboard
            <span class="status-badge">
                <span class="status-dot"></span>
                LIVE
            </span>
            </h1>
            <div class="control-group" style="display: flex; gap: 0.5rem; margin-left: auto;">
            <button id="resume-btn" class="theme-btn" style="display: none; background: var(--success); color: white; border: none;">▶️ Resume Bot</button>
            <button id="pause-btn" class="theme-btn" style="background: var(--warning); color: white; border: none;">⏸ Pause Bot</button>
            <button id="logout-btn" class="theme-btn">🚪 Logout</button>
            <div class="theme-selector">

            <button class="theme-btn" data-theme="light">☀️ Light</button>
            <button class="theme-btn active" data-theme="system">💻 System</button>
            <button class="theme-btn" data-theme="dark">🌙 Dark</button>
        </div>
    </div>

    <div class="system-bar" id="system-bar">
        <div class="system-pill">
            <span class="system-pill-dot" id="system-status-dot"></span>
            <span class="system-pill-label">System</span>
            <span id="system-status-text">Starting…</span>
        </div>
        <div class="system-pill">
            <span class="system-pill-label">Uptime</span>
            <span id="system-uptime">0:00:00</span>
        </div>
        <div class="system-pill">
            <span class="system-pill-label">Positions</span>
            <span id="system-open-positions">0 open / 0 orders</span>
        </div>
        <div class="system-pill">
            <span class="system-pill-label">Mode</span>
            <span id="system-mode">PAPER</span>
        </div>
    </div>

    <div class="container">
        <div class="tab-bar">
            <button class="tab-btn active" data-tab="paper-tab">Demo / Paper Trading</button>
            <button class="tab-btn" data-tab="realtime-tab">Real Broker Trading</button>
            <button class="tab-btn" data-tab="charts-tab">📈 Interactive Charts</button>
        </div>

        <div class="tab-panel active" id="paper-tab">
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">💰 Account Balance</div>
                    <div class="metric-value" id="balance">$0.00</div>
                    <div class="metric-change" id="balance-change">0.00%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">📈 Total PnL</div>
                    <div class="metric-value" id="total-pnl">$0.00</div>
                    <div class="metric-change" id="total-pnl-pct">0.00%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">📅 Daily PnL</div>
                    <div class="metric-value" id="daily-pnl">$0.00</div>
                    <div class="metric-change" id="daily-pnl-pct">0.00%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">🎯 Win Rate</div>
                    <div class="metric-value" id="win-rate">0%</div>
                    <div class="metric-change" id="total-trades">0 trades</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">📊 Open Positions</div>
                    <div class="metric-value" id="open-positions">0</div>
                    <div class="metric-change" id="unrealized-pnl">$0.00 unrealized</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">⚠️ Circuit Breaker</div>
                    <div class="metric-value" id="circuit-breaker">CLOSED</div>
                    <div class="metric-change" id="trading-allowed">Trading Allowed</div>
                </div>
            </div>

            <div class="section">
                <div class="section-header">📊 Open Positions</div>
                <div id="positions-container">
                    <div class="empty-state">No open positions</div>
                </div>
            </div>

            <div class="section">
                <div class="section-header">📝 Recent Trades</div>
                <div id="trades-container">
                    <div class="empty-state">No recent trades</div>
                </div>
            </div>

            <div class="section">
                <div class="section-header">🔔 Recent Alerts</div>
                <div id="alerts-container">
                    <div class="empty-state">No recent alerts</div>
                </div>
            </div>

            <div class="section">
                <div class="section-header">📊 Strategy Performance Attribution (PnL by Signal)</div>
                <div style="display: flex; flex-direction: row; flex-wrap: wrap; gap: 2rem; align-items: center;">
                    <div style="flex: 1; min-width: 300px; max-width: 400px; margin: 0 auto;">
                        <canvas id="attribution-chart"></canvas>
                    </div>
                    <div id="attribution-container" style="flex: 2; display: flex; flex-wrap: wrap; gap: 1rem; justify-content: space-around; padding: 1rem;">
                        <div class="empty-state">No attribution data yet</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="tab-panel" id="realtime-tab">
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">🏦 Active Broker</div>
                    <div class="metric-value" id="active-broker">PaperBroker</div>
                    <div class="metric-change" id="active-mode">paper</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">🧾 Real Broker Provider</div>
                    <div class="metric-value" id="real-broker-provider">oanda</div>
                    <div class="metric-change" id="real-broker-ready">Not ready</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">📰 News Sentiment</div>
                    <div class="metric-value" id="sentiment-label">NEUTRAL</div>
                    <div class="metric-change" id="sentiment-score">0.00 across 0 articles</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">💱 EUR/USD</div>
                    <div class="metric-value" id="eurusd-rate">n/a</div>
                    <div class="metric-change" id="source-health">Sources idle</div>
                </div>
            </div>

            <div class="section">
                <div class="section-header">🔌 Real Broker Status</div>
                <div id="broker-status-container">
                    <div class="empty-state">No broker status yet</div>
                </div>
            </div>

            <div class="section">
                <div class="section-header">🌐 Market Context</div>
                <div id="market-context-container">
                    <div class="empty-state">No market context yet</div>
                </div>
            </div>

            <div class="section">
                <div class="section-header">🧠 Latest Signals</div>
                <div id="signals-container">
                    <div class="empty-state">No signals yet</div>
                </div>
            </div>

            <div class="section">
                <div class="section-header">🔗 Market Correlation Matrix</div>
                <div id="correlation-container">
                    <div class="empty-state">Loading correlation data...</div>
                </div>
            </div>
        </div>

        <div class="tab-panel" id="charts-tab">
            <div class="section">
                <div class="section-header">
                    📈 Price Charts
                    <div style="margin-left: auto; display: flex; gap: 0.5rem;">
                        <select id="chart-symbol" style="padding: 0.25rem; border-radius: 4px; background: var(--bg-secondary); color: var(--text-primary); border: 1px solid var(--border);">
                            <optgroup label="Crypto">
                                <option value="BTCUSD">BTC/USD</option>
                                <option value="ETHUSD">ETH/USD</option>
                            </optgroup>
                            <optgroup label="Forex">
                                <option value="EURUSD">EUR/USD</option>
                                <option value="GBPUSD">GBP/USD</option>
                            </optgroup>
                            <optgroup label="Indices & Stocks">
                                <option value="NIFTY50">Nifty 50</option>
                                <option value="AAPL">Apple (AAPL)</option>
                                <option value="RELIANCE">Reliance</option>
                            </optgroup>
                            <optgroup label="Commodities">
                                <option value="GOLD">Gold</option>
                                <option value="SILVER">Silver</option>
                            </optgroup>
                        </select>
                        <select id="chart-timeframe" style="padding: 0.25rem; border-radius: 4px; background: var(--bg-secondary); color: var(--text-primary); border: 1px solid var(--border);">
                            <option value="1m">1m</option>
                            <option value="5m">5m</option>
                            <option value="1h" selected>1h</option>
                            <option value="1D">1D</option>
                        </select>
                    </div>
                </div>
                <div id="tv-chart-container" style="height: 500px; width: 100%;"></div>
            </div>

            <div class="section">
                <div class="section-header">
                    ⚙️ Strategy Settings & Tuning
                    <button id="tune-btn" class="login-btn" style="width: auto; padding: 0.25rem 1rem; margin: 0 0 0 auto;">
                        🛠 Tune Current Symbol
                    </button>
                </div>
                <div id="params-container">
                    <div class="empty-state">Load parameters to view tuned settings</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Auth management
        const auth = {
            getToken: () => localStorage.getItem('dashboard_token'),
            setToken: (token) => localStorage.setItem('dashboard_token', token),
            clearToken: () => localStorage.removeItem('dashboard_token'),
            isLoggedIn: () => !!localStorage.getItem('dashboard_token')
        };

        async function login(username, password) {
            const formData = new FormData();
            formData.append('username', username);
            formData.append('password', password);

            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    const data = await response.json();
                    auth.setToken(data.access_token);
                    document.getElementById('login-overlay').style.display = 'none';
                    document.getElementById('login-error').style.display = 'none';
                    connectWebSocket();
                    chartManager.loadData();
                } else {
                    document.getElementById('login-error').style.display = 'block';
                }
            } catch (error) {
                console.error('Login error:', error);
                document.getElementById('login-error').style.display = 'block';
            }
        }

        async function authenticatedFetch(url, options = {}) {
            const token = auth.getToken();
            const headers = {
                ...options.headers,
                'Authorization': `Bearer ${token}`
            };

            const response = await fetch(url, { ...options, headers });
            if (response.status === 401) {
                auth.clearToken();
                document.getElementById('login-overlay').style.display = 'flex';
                if (socket) socket.close();
                return null;
            }
            return response;
        }

        // Handle login form
        document.getElementById('login-form').addEventListener('submit', (e) => {
            e.preventDefault();
            const user = document.getElementById('username').value;
            const pass = document.getElementById('password').value;
            login(user, pass);
        });

        // Check auth on load
        if (auth.isLoggedIn()) {
            document.getElementById('login-overlay').style.display = 'none';
            loadTunedParams();
            loadCorrelationMatrix();
        }

        async function loadCorrelationMatrix() {
            try {
                const response = await authenticatedFetch('/api/correlation');
                if (!response) return;
                const data = await response.json();
                const container = document.getElementById('correlation-container');
                
                if (!data.symbols || data.symbols.length === 0) {
                    container.innerHTML = '<div class="empty-state">No correlation data available. Bot needs to refresh market context first.</div>';
                    return;
                }

                let html = '<table class="table" style="table-layout: fixed;"><thead><tr><th></th>';
                data.symbols.forEach(s => {
                    html += `<th>${s}</th>`;
                });
                html += '</tr></thead><tbody>';

                data.symbols.forEach((rowSym, i) => {
                    html += `<tr><td><strong>${rowSym}</strong></td>`;
                    data.symbols.forEach((colSym, j) => {
                        const val = data.values[i][j];
                        let bg = 'transparent';
                        let color = 'inherit';
                        
                        if (i === j) {
                            bg = 'var(--bg-secondary)';
                        } else if (val > 0.8) {
                            bg = 'rgba(239, 68, 68, 0.2)'; // Light red
                            color = 'var(--danger)';
                        } else if (val < -0.8) {
                            bg = 'rgba(34, 197, 94, 0.2)'; // Light green
                            color = 'var(--success)';
                        }
                        
                        html += `<td style="background: ${bg}; color: ${color}; text-align: center;">${val.toFixed(2)}</td>`;
                    });
                    html += '</tr>';
                });

                html += '</tbody></table>';
                container.innerHTML = html;
            } catch (error) {
                console.error('Error loading correlation matrix:', error);
            }
        }

        async function loadTunedParams() {
            try {
                const response = await authenticatedFetch('/api/params');
                if (!response) return;
                const params = await response.json();
                const container = document.getElementById('params-container');
                
                if (Object.keys(params).length === 0) {
                    container.innerHTML = '<div class="empty-state">No tuned parameters found. Run tuning to optimize!</div>';
                    return;
                }

                let html = `
                    <div style="margin-bottom: 1rem; display: flex; align-items: center;">
                        <span>Interactive Parameter Editor</span>
                        <button onclick="saveParameters()" class="login-btn" style="width: auto; padding: 0.25rem 1rem; margin-left: auto; background: var(--success);">
                            💾 Save Parameter Changes
                        </button>
                    </div>
                    <table class="table" id="params-table">
                        <thead>
                            <tr>
                                <th>Symbol</th>
                                <th>Indicator Settings (Editable)</th>
                            </tr>
                        </thead>
                        <tbody>
                `;

                for (const [symbol, settings] of Object.entries(params)) {
                    let settingsHtml = '';
                    for (const [k, v] of Object.entries(settings)) {
                        settingsHtml += `
                            <div style="display: inline-block; margin: 4px; padding: 4px; background: var(--bg-secondary); border-radius: 4px; border: 1px solid var(--border);">
                                <label style="font-size: 0.7rem; color: var(--text-secondary); display: block;">${k}</label>
                                <input type="number" step="any" data-symbol="${symbol}" data-key="${k}" value="${v}" 
                                    style="width: 60px; background: transparent; color: var(--text-primary); border: none; font-weight: bold; font-size: 0.85rem;">
                            </div>
                        `;
                    }
                    
                    html += `
                        <tr>
                            <td style="vertical-align: top; padding-top: 1rem;"><strong>${symbol}</strong></td>
                            <td>${settingsHtml}</td>
                        </tr>
                    `;
                }

                html += '</tbody></table>';
                container.innerHTML = html;
            } catch (error) {
                console.error('Error loading params:', error);
            }
        }

        async function saveParameters() {
            const inputs = document.querySelectorAll('#params-table input');
            const newParams = {};
            
            inputs.forEach(input => {
                const symbol = input.dataset.symbol;
                const key = input.dataset.key;
                const val = parseFloat(input.value);
                
                if (!newParams[symbol]) newParams[symbol] = {};
                newParams[symbol][key] = val;
            });

            try {
                const response = await authenticatedFetch('/api/params', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(newParams)
                });

                if (response && response.ok) {
                    alert('Parameters updated successfully and applied to live strategy!');
                    loadTunedParams();
                } else {
                    alert('Failed to save parameters. Check console for errors.');
                }
            } catch (error) {
                console.error('Error saving parameters:', error);
                alert('Error saving parameters.');
            }
        }

        async function runTuning() {
            const symbol = document.getElementById('chart-symbol').value;
            const btn = document.getElementById('tune-btn');
            const originalText = btn.textContent;
            
            try {
                btn.disabled = true;
                btn.textContent = '⌛ Tuning Started...';
                
                const response = await authenticatedFetch(`/api/tune/${symbol}`, { method: 'POST' });
                if (response && response.ok) {
                    alert(`Tuning started for ${symbol} in the background. It may take a minute. Check server logs for progress.`);
                }
            } catch (error) {
                console.error('Error starting tuning:', error);
            } finally {
                setTimeout(() => {
                    btn.disabled = false;
                    btn.textContent = originalText;
                }, 5000);
            }
        }

        async function pauseBot() {
            const response = await authenticatedFetch('/api/bot/pause', { method: 'POST' });
            if (response && response.ok) {
                console.log('Bot paused');
            }
        }

        async function resumeBot() {
            const response = await authenticatedFetch('/api/bot/resume', { method: 'POST' });
            if (response && response.ok) {
                console.log('Bot resumed');
            }
        }

        async function closePosition(symbol) {
            if (confirm(`Are you sure you want to close the ${symbol} position manually?`)) {
                const response = await authenticatedFetch(`/api/positions/close/${symbol}`, { method: 'POST' });
                if (response && response.ok) {
                    alert(`Closing order for ${symbol} submitted.`);
                }
            }
        }

        function logout() {
            auth.clearToken();
            location.reload();
        }

        document.getElementById('tune-btn').addEventListener('click', runTuning);
        document.getElementById('pause-btn').addEventListener('click', pauseBot);
        document.getElementById('resume-btn').addEventListener('click', resumeBot);
        document.getElementById('logout-btn').addEventListener('click', logout);

        // Theme management
        const themeButtons = document.querySelectorAll('.theme-btn');
        const tabButtons = document.querySelectorAll('.tab-btn');
        const html = document.documentElement;

        function setTheme(theme) {
            localStorage.setItem('theme', theme);
            themeButtons.forEach(btn => {
                btn.classList.toggle('active', btn.dataset.theme === theme);
            });

            if (theme === 'system') {
                const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                html.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
            } else {
                html.setAttribute('data-theme', theme);
            }

            // Update chart theme
            if (typeof chartManager !== 'undefined' && chartManager.chart) {
                chartManager.applyTheme(theme);
            }
            if (typeof attrChartManager !== 'undefined' && attrChartManager.chart) {
                attrChartManager.applyTheme(theme);
            }
        }

        themeButtons.forEach(btn => {
            btn.addEventListener('click', () => setTheme(btn.dataset.theme));
        });

        function setTab(tabId) {
            tabButtons.forEach(btn => {
                btn.classList.toggle('active', btn.dataset.tab === tabId);
            });
            document.querySelectorAll('.tab-panel').forEach(panel => {
                panel.classList.toggle('active', panel.id === tabId);
            });

            if (tabId === 'realtime-tab') {
                loadCorrelationMatrix();
            }
        }

        tabButtons.forEach(btn => {
            btn.addEventListener('click', () => setTab(btn.dataset.tab));
        });

        // Initialize theme
        const savedTheme = localStorage.getItem('theme') || 'system';
        setTheme(savedTheme);

        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (localStorage.getItem('theme') === 'system') {
                html.setAttribute('data-theme', e.matches ? 'dark' : 'light');
            }
        });

        // Update dashboard data
        function formatCurrency(value) {
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD',
                minimumFractionDigits: 2
            }).format(value);
        }

        function formatPercent(value) {
            const sign = value >= 0 ? '+' : '';
            return `${sign}${value.toFixed(2)}%`;
        }

        function updateDashboard(data) {
            const contextValues = Object.values(data.market_context || {});
            const primaryContext = contextValues[0] || null;
            const brokerStatus = data.broker_status || {};
            const system = data.system || {};

            // Update metrics
            document.getElementById('balance').textContent = formatCurrency(data.account.account_balance);
            document.getElementById('balance-change').textContent = formatPercent(data.account.total_return_pct);
            document.getElementById('balance-change').className = 'metric-change ' + (data.account.total_return_pct >= 0 ? 'positive' : 'negative');

            document.getElementById('total-pnl').textContent = formatCurrency(data.account.total_return);
            document.getElementById('total-pnl').className = 'metric-value ' + (data.account.total_return >= 0 ? 'positive' : 'negative');
            document.getElementById('total-pnl-pct').textContent = formatPercent(data.account.total_return_pct);
            document.getElementById('total-pnl-pct').className = 'metric-change ' + (data.account.total_return_pct >= 0 ? 'positive' : 'negative');

            document.getElementById('daily-pnl').textContent = formatCurrency(data.account.daily_pnl);
            document.getElementById('daily-pnl').className = 'metric-value ' + (data.account.daily_pnl >= 0 ? 'positive' : 'negative');
            document.getElementById('daily-pnl-pct').textContent = formatPercent(data.account.daily_pnl_pct);
            document.getElementById('daily-pnl-pct').className = 'metric-change ' + (data.account.daily_pnl_pct >= 0 ? 'positive' : 'negative');

            document.getElementById('win-rate').textContent = data.performance.win_rate.toFixed(1) + '%';
            document.getElementById('total-trades').textContent = data.performance.total_trades + ' trades';

            document.getElementById('open-positions').textContent = data.positions.length;
            document.getElementById('unrealized-pnl').textContent = formatCurrency(data.account.unrealized_pnl) + ' unrealized';
            document.getElementById('unrealized-pnl').className = 'metric-change ' + (data.account.unrealized_pnl >= 0 ? 'positive' : 'negative');

            document.getElementById('circuit-breaker').textContent = data.risk.circuit_breaker_state.toUpperCase();
            document.getElementById('trading-allowed').textContent = data.risk.trading_allowed ? 'Trading Allowed ✅' : 'Trading Blocked ⛔';

            document.getElementById('active-broker').textContent = brokerStatus.active_broker || 'Unknown';
            document.getElementById('active-mode').textContent = `Mode: ${(brokerStatus.active_mode || 'unknown').toUpperCase()} | Config: ${(brokerStatus.execution_mode || 'paper').toUpperCase()}`;
            document.getElementById('real-broker-provider').textContent = (brokerStatus.real_broker_provider || 'n/a').toUpperCase();
            document.getElementById('real-broker-ready').textContent = brokerStatus.real_broker_ready ? 'Credentials ready' : 'Not ready';
            document.getElementById('real-broker-ready').className = 'metric-change ' + (brokerStatus.real_broker_ready ? 'positive' : 'negative');

            document.getElementById('sentiment-label').textContent = primaryContext ? primaryContext.sentiment_label : 'NEUTRAL';
            document.getElementById('sentiment-score').textContent = primaryContext
                ? `${primaryContext.sentiment_score.toFixed(2)} across ${primaryContext.article_count} articles`
                : '0.00 across 0 articles';
            document.getElementById('sentiment-score').className = 'metric-change ' + (
                primaryContext && primaryContext.sentiment_score < 0 ? 'negative' : 'positive'
            );

            document.getElementById('eurusd-rate').textContent = primaryContext && primaryContext.eurusd_rate
                ? primaryContext.eurusd_rate.toFixed(5)
                : 'n/a';
            document.getElementById('source-health').textContent = primaryContext
                ? `News: ${primaryContext.news_status} | FX: ${primaryContext.forex_status}`
                : 'Sources idle';

            // Update system status bar
            document.getElementById('system-status-text').textContent =
                system.status === 'running' ? 'Running' : (system.status || 'Unknown');
            document.getElementById('system-uptime').textContent = system.uptime || '0:00:00';
            document.getElementById('system-open-positions').textContent =
                `${system.open_positions ?? 0} open / ${system.open_orders ?? 0} orders`;
            document.getElementById('system-mode').textContent =
                `${(brokerStatus.execution_mode || 'paper').toUpperCase()} • ${(brokerStatus.active_broker || 'Unknown')}`;

            const systemDot = document.getElementById('system-status-dot');
            if (system.status === 'running' && data.risk && data.risk.trading_allowed) {
                systemDot.classList.remove('danger');
            } else {
                systemDot.classList.add('danger');
            }

            // Update pause/resume buttons
            if (system.is_paused) {
                document.getElementById('pause-btn').style.display = 'none';
                document.getElementById('resume-btn').style.display = 'block';
                document.getElementById('system-status-text').textContent = 'PAUSED';
            } else {
                document.getElementById('pause-btn').style.display = 'block';
                document.getElementById('resume-btn').style.display = 'none';
            }

            // Update broker status
            const brokerStatusContainer = document.getElementById('broker-status-container');
            if (Object.keys(brokerStatus).length > 0) {
                let html = '<table><thead><tr><th>Field</th><th>Value</th></tr></thead><tbody>';
                html += `<tr><td><strong>Execution mode</strong></td><td>${(brokerStatus.execution_mode || 'paper').toUpperCase()}</td></tr>`;
                html += `<tr><td><strong>Active broker</strong></td><td>${brokerStatus.active_broker || 'Unknown'}</td></tr>`;
                html += `<tr><td><strong>Connected</strong></td><td>${brokerStatus.connected ? 'Yes' : 'No'}</td></tr>`;
                html += `<tr><td><strong>Real broker provider</strong></td><td>${(brokerStatus.real_broker_provider || 'n/a').toUpperCase()}</td></tr>`;
                html += `<tr><td><strong>Implemented</strong></td><td>${brokerStatus.real_broker_implemented ? 'Yes' : 'No'}</td></tr>`;
                html += `<tr><td><strong>Ready</strong></td><td>${brokerStatus.real_broker_ready ? 'Yes' : 'No'}</td></tr>`;
                html += '</tbody></table>';
                if (brokerStatus.required_credentials) {
                    html += '<div style="margin-top: 1rem;"><strong>Credential checks</strong><table style="margin-top: 0.75rem;"><thead><tr><th>Credential</th><th>Status</th></tr></thead><tbody>';
                    Object.entries(brokerStatus.required_credentials).forEach(([name, present]) => {
                        html += `<tr><td>${name}</td><td class="${present ? 'positive' : 'negative'}">${present ? 'Present' : 'Missing'}</td></tr>`;
                    });
                    html += '</tbody></table></div>';
                }
                html += `<div style="margin-top: 1rem; color: var(--text-secondary);">${brokerStatus.status_message || ''}</div>`;
                brokerStatusContainer.innerHTML = html;
            } else {
                brokerStatusContainer.innerHTML = '<div class="empty-state">No broker status yet</div>';
            }

            // Update market context
            const contextContainer = document.getElementById('market-context-container');
            if (contextValues.length > 0) {
                let html = '<table><thead><tr><th>Symbol</th><th>Sentiment</th><th>Articles</th><th>EUR/USD</th><th>Providers</th><th>Updated</th></tr></thead><tbody>';
                contextValues.forEach(ctx => {
                    const scoreClass = ctx.sentiment_score >= 0 ? 'positive' : 'negative';
                    html += `<tr>
                        <td><strong>${ctx.symbol}</strong></td>
                        <td class="${scoreClass}">${ctx.sentiment_label} (${ctx.sentiment_score.toFixed(2)})</td>
                        <td>${ctx.article_count}</td>
                        <td>${ctx.eurusd_rate ? ctx.eurusd_rate.toFixed(5) : 'n/a'}</td>
                        <td>${ctx.news_provider} / ${ctx.forex_provider}</td>
                        <td>${ctx.last_updated ? new Date(ctx.last_updated).toLocaleTimeString() : 'n/a'}</td>
                    </tr>`;
                });
                html += '</tbody></table>';
                
                if (primaryContext && primaryContext.sentiment_reason) {
                    html += `<div style="margin-top: 1rem; padding: 0.75rem; background: var(--bg-secondary); border-left: 4px solid var(--accent); border-radius: 0 4px 4px 0;">
                        <strong>🤖 AI Reasoning:</strong> ${primaryContext.sentiment_reason}
                    </div>`;
                }

                if (primaryContext && primaryContext.headlines && primaryContext.headlines.length > 0) {
                    html += '<div style="margin-top: 1rem;"><strong>Headlines</strong><ul style="margin: 0.75rem 0 0 1.25rem;">';
                    primaryContext.headlines.forEach(headline => {
                        html += `<li style="margin-bottom: 0.4rem;">${headline}</li>`;
                    });
                    html += '</ul></div>';
                }
                contextContainer.innerHTML = html;
            } else {
                contextContainer.innerHTML = '<div class="empty-state">No market context yet</div>';
            }

            // Update latest signals
            const signalsContainer = document.getElementById('signals-container');
            if (data.latest_signals.length > 0) {
                let html = '<table><thead><tr><th>Time</th><th>Symbol</th><th>Side</th><th>Strength</th><th>Sentiment</th><th>RSI</th><th>Close</th></tr></thead><tbody>';
                data.latest_signals.slice(0, 10).forEach(signal => {
                    const time = new Date(signal.timestamp).toLocaleTimeString();
                    const signalClass = signal.side === 'buy' ? 'badge-success' : 'badge-danger';
                    const sentimentClass = signal.sentiment_score >= 0 ? 'positive' : 'negative';
                    html += `<tr>
                        <td>${time}</td>
                        <td><strong>${signal.symbol}</strong></td>
                        <td><span class="badge ${signalClass}">${signal.side.toUpperCase()}</span></td>
                        <td>${signal.strength.toFixed(2)}</td>
                        <td class="${sentimentClass}">${signal.sentiment_label} (${signal.sentiment_score.toFixed(2)})</td>
                        <td>${signal.rsi ? signal.rsi.toFixed(2) : 'n/a'}</td>
                        <td>${signal.close ? formatCurrency(signal.close) : 'n/a'}</td>
                    </tr>`;
                });
                html += '</tbody></table>';
                signalsContainer.innerHTML = html;
            } else {
                signalsContainer.innerHTML = '<div class="empty-state">No signals yet</div>';
            }

            // Update positions
            const positionsContainer = document.getElementById('positions-container');
            if (data.positions.length > 0) {
                let html = '<table><thead><tr><th>Symbol</th><th>Side</th><th>Size</th><th>Entry</th><th>Current</th><th>PnL</th><th>Duration</th><th>Action</th></tr></thead><tbody>';
                data.positions.forEach(pos => {
                    const pnlClass = pos.unrealized_pnl >= 0 ? 'positive' : 'negative';
                    const sign = pos.unrealized_pnl >= 0 ? '+' : '';
                    html += `<tr>
                        <td><strong>${pos.symbol}</strong></td>
                        <td><span class="badge ${pos.side === 'buy' ? 'badge-success' : 'badge-danger'}">${pos.side.toUpperCase()}</span></td>
                        <td>${pos.size.toFixed(4)}</td>
                        <td>${formatCurrency(pos.entry_price)}</td>
                        <td>${formatCurrency(pos.current_price)}</td>
                        <td class="${pnlClass}">${sign}${formatCurrency(pos.unrealized_pnl)} (${sign}${pos.unrealized_pnl_pct.toFixed(2)}%)</td>
                        <td>${pos.duration}</td>
                        <td><button onclick="closePosition('${pos.symbol}')" class="badge badge-danger" style="border:none; cursor:pointer;">Close</button></td>
                    </tr>`;
                });
                html += '</tbody></table>';
                positionsContainer.innerHTML = html;
            } else {
                positionsContainer.innerHTML = '<div class="empty-state">No open positions</div>';
            }

            // Update trades
            const tradesContainer = document.getElementById('trades-container');
            if (data.recent_trades.length > 0) {
                let html = '<table><thead><tr><th>Time</th><th>Symbol</th><th>Side</th><th>Quantity</th><th>Price</th><th>PnL</th></tr></thead><tbody>';
                data.recent_trades.slice(0, 10).forEach(trade => {
                    const time = new Date(trade.timestamp).toLocaleTimeString();
                    const pnlClass = trade.pnl >= 0 ? 'positive' : 'negative';
                    const sign = trade.pnl >= 0 ? '+' : '';
                    html += `<tr>
                        <td>${time}</td>
                        <td><strong>${trade.symbol}</strong></td>
                        <td><span class="badge ${trade.side === 'buy' ? 'badge-success' : 'badge-danger'}">${trade.side.toUpperCase()}</span></td>
                        <td>${trade.quantity.toFixed(4)}</td>
                        <td>${formatCurrency(trade.price)}</td>
                        <td class="${pnlClass}">${sign}${formatCurrency(trade.pnl)}</td>
                    </tr>`;
                });
                html += '</tbody></table>';
                tradesContainer.innerHTML = html;
            } else {
                tradesContainer.innerHTML = '<div class="empty-state">No recent trades</div>';
            }

            // Update alerts
            const alertsContainer = document.getElementById('alerts-container');
            if (data.alerts.length > 0) {
                let html = '';
                data.alerts.slice(0, 10).forEach(alert => {
                    const time = new Date(alert.timestamp).toLocaleTimeString();
                    html += `<div class="alert-item">
                        <span class="alert-time">[${time}]</span>
                        <span class="badge badge-${alert.level === 'error' || alert.level === 'critical' ? 'danger' : alert.level === 'warning' ? 'warning' : 'info'}">${alert.level.toUpperCase()}</span>
                        ${alert.message}
                    </div>`;
                });
                alertsContainer.innerHTML = html;
            } else {
                alertsContainer.innerHTML = '<div class="empty-state">No recent alerts</div>';
            }

            // Update performance attribution
            const attributionContainer = document.getElementById('attribution-container');
            if (data.performance && data.performance.attribution && Object.keys(data.performance.attribution).length > 0) {
                let html = '';
                const attribution = data.performance.attribution;
                
                // Update Chart.js pie chart
                attrChartManager.update(attribution);

                Object.entries(attribution).forEach(([type, pnl]) => {
                    if (pnl === 0) return; // Skip components with no history
                    const pnlClass = pnl >= 0 ? 'positive' : 'negative';
                    const sign = pnl >= 0 ? '+' : '';
                    
                    html += `
                        <div class="metric-card" style="flex: 1; min-width: 150px; text-align: center;">
                            <div class="metric-label" style="justify-content: center;">${type.toUpperCase()}</div>
                            <div class="metric-value ${pnlClass}" style="font-size: 1.25rem;">${sign}${formatCurrency(pnl)}</div>
                        </div>
                    `;
                });
                
                if (html === '') {
                    attributionContainer.innerHTML = '<div class="empty-state">No realized trades yet to attribute performance</div>';
                } else {
                    attributionContainer.innerHTML = html;
                }
            } else {
                attributionContainer.innerHTML = '<div class="empty-state">No attribution data available</div>';
            }
        }

        // Chart management
        class ChartManager {
            constructor() {
                this.chart = null;
                this.candleSeries = null;
                this.currentSymbol = 'BTCUSD';
                this.currentTimeframe = '1h';
                this.init();
            }

            init() {
                const container = document.getElementById('tv-chart-container');
                const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
                
                this.chart = LightweightCharts.createChart(container, {
                    layout: {
                        background: { color: isDark ? '#16191f' : '#ffffff' },
                        textColor: isDark ? '#9ca3af' : '#1a1a1a',
                    },
                    grid: {
                        vertLines: { color: isDark ? '#22262e' : '#e0e0e0' },
                        horzLines: { color: isDark ? '#22262e' : '#e0e0e0' },
                    },
                    timeScale: {
                        timeVisible: true,
                        secondsVisible: false,
                    },
                });

                this.candleSeries = this.chart.addCandlestickSeries();
                
                // Handle resize
                window.addEventListener('resize', () => {
                    this.chart.applyOptions({ width: container.clientWidth });
                });

                // Listen for symbol/timeframe changes
                document.getElementById('chart-symbol').addEventListener('change', (e) => {
                    this.currentSymbol = e.target.value;
                    this.loadData();
                });
                document.getElementById('chart-timeframe').addEventListener('change', (e) => {
                    this.currentTimeframe = e.target.value;
                    this.loadData();
                });

                this.loadData();
            }

            async loadData() {
                try {
                    const response = await authenticatedFetch(`/api/candles/${this.currentSymbol}?timeframe=${this.currentTimeframe}`);
                    if (!response) return;
                    const data = await response.json();
                    if (Array.isArray(data)) {
                        this.candleSeries.setData(data);
                    }
                } catch (error) {
                    console.error('Error loading chart data:', error);
                }
            }

            updateTicker(ticker) {
                if (ticker.symbol !== this.currentSymbol) return;
                
                const timestamp = Math.floor(new Date(ticker.timestamp).getTime() / 1000);
                this.candleSeries.update({
                    time: timestamp,
                    close: ticker.last_price,
                    // Note: In a real tick feed, we'd need high/low/open for the current bar
                    // For now, we'll just update the close price
                });
            }

            applyTheme(theme) {
                const isDark = theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
                this.chart.applyOptions({
                    layout: {
                        background: { color: isDark ? '#16191f' : '#ffffff' },
                        textColor: isDark ? '#9ca3af' : '#1a1a1a',
                    },
                    grid: {
                        vertLines: { color: isDark ? '#22262e' : '#e0e0e0' },
                        horzLines: { color: isDark ? '#22262e' : '#e0e0e0' },
                    }
                });
            }
        }

        const chartManager = new ChartManager();

        // Attribution Chart management
        class AttributionChartManager {
            constructor() {
                this.chart = null;
                this.init();
            }

            init() {
                const ctx = document.getElementById('attribution-chart').getContext('2d');
                const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
                
                this.chart = new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: [],
                        datasets: [{
                            data: [],
                            backgroundColor: [
                                '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444'
                            ],
                            borderWidth: 0
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: { color: isDark ? '#9ca3af' : '#1a1a1a' }
                            }
                        }
                    }
                });
            }

            update(attribution) {
                if (!attribution || Object.keys(attribution).length === 0) return;
                
                const labels = Object.keys(attribution).map(k => k.toUpperCase());
                const data = Object.values(attribution);
                
                this.chart.data.labels = labels;
                this.chart.data.datasets[0].data = data;
                this.chart.update();
            }

            applyTheme(theme) {
                const isDark = theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
                this.chart.options.plugins.legend.labels.color = isDark ? '#9ca3af' : '#1a1a1a';
                this.chart.update();
            }
        }

        const attrChartManager = new AttributionChartManager();

        // WebSocket management
        let socket = null;
        let reconnectTimer = null;

        function connectWebSocket() {
            if (!auth.isLoggedIn()) return;

            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            console.log('Connecting to WebSocket...', wsUrl);
            // Pass token via subprotocol
            socket = new WebSocket(wsUrl, [`bearer.${auth.getToken()}`]);

            socket.onopen = () => {
                console.log('WebSocket connected');
                document.getElementById('system-status-text').textContent = 'Running';
                if (reconnectTimer) {
                    clearTimeout(reconnectTimer);
                    reconnectTimer = null;
                }
            };

            socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    updateDashboard(data);
                    
                    // Update chart if ticker data is present
                    if (data.market_context) {
                        Object.values(data.market_context).forEach(ctx => {
                            if (ctx.symbol) chartManager.updateTicker({
                                symbol: ctx.symbol,
                                last_price: ctx.last_price || ctx.eurusd_rate,
                                timestamp: ctx.last_updated || new Date().toISOString()
                            });
                        });
                    }
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };

            socket.onclose = () => {
                console.log('WebSocket disconnected');
                document.getElementById('system-status-text').textContent = 'Disconnected (Reconnecting...)';
                // Attempt to reconnect after 3 seconds
                reconnectTimer = setTimeout(connectWebSocket, 3000);
            };

            socket.onerror = (error) => {
                console.error('WebSocket error:', error);
                socket.close();
            };
        }

        // Initial connection
        if (auth.isLoggedIn()) {
            connectWebSocket();
        }
    </script>
</body>
</html>
"""

    async def run(self):
        """Run the web dashboard server."""
        import uvicorn

        logger.info(f"Starting web dashboard at http://{self.host}:{self.port}")
        config = uvicorn.Config(
            self.app, host=self.host, port=self.port, log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()


# Example usage
async def main():
    from execution.paper_broker import PaperBroker
    from strategy.signal_strategy import TechnicalSignalStrategy
    from risk.circuit_breaker import CircuitBreaker
    from monitoring.pnl_tracker import PnLTracker
    from monitoring.alerts import AlertManager

    # Initialize components
    pnl_tracker = PnLTracker(initial_balance=10000.0)
    alert_manager = AlertManager()
    broker = PaperBroker(initial_balance=10000.0)
    await broker.connect()
    strategy = TechnicalSignalStrategy()
    circuit_breaker = CircuitBreaker()

    # Create dashboard data
    dashboard_data = DashboardData(
        pnl_tracker=pnl_tracker,
        alert_manager=alert_manager,
        broker=broker,
        strategy=strategy,
        circuit_breaker=circuit_breaker,
    )

    # Create and run web dashboard
    web_dashboard = WebDashboard(dashboard_data)
    await web_dashboard.run()


if __name__ == "__main__":
    asyncio.run(main())
