"""
Prometheus metrics exporter for the trading bot.
Exposes real-time operational and financial metrics.
"""

from prometheus_client import start_http_server, Gauge, Counter, Histogram
from loguru import logger
from typing import Dict

# 1. Define Metrics
PNL_TOTAL = Gauge('trading_bot_pnl_total', 'Total realized PnL in USD')
PNL_DAILY = Gauge('trading_bot_pnl_daily', 'Daily realized PnL in USD')
EQUITY_TOTAL = Gauge('trading_bot_equity_total', 'Current total equity in USD')
POSITIONS_ACTIVE = Gauge('trading_bot_positions_active', 'Number of currently open positions')
ORDERS_TOTAL = Counter('trading_bot_orders_total', 'Total number of orders placed', ['symbol', 'side', 'type'])
TRADES_TOTAL = Counter('trading_bot_trades_total', 'Total number of trades executed', ['symbol', 'side'])
AI_CONFIDENCE = Gauge('trading_bot_ai_confidence', 'LSTM prediction confidence score', ['symbol'])
SENTIMENT_SCORE = Gauge('trading_bot_sentiment_score', 'Current market sentiment score', ['symbol'])
API_LATENCY = Histogram('trading_bot_api_latency_seconds', 'Latency of external API calls', ['provider'])

class MetricsExporter:
    """
    Manages the Prometheus metrics server and updates.
    """

    def __init__(self, port: int = 9090):
        self.port = port
        self.server_started = False

    def start(self):
        """Start the Prometheus metrics server."""
        if not self.server_started:
            try:
                start_http_server(self.port)
                self.server_started = True
                logger.info(f"Prometheus metrics exporter started on port {self.port}")
            except Exception as e:
                logger.error(f"Failed to start Prometheus server: {e}")

    def update_financials(self, equity: float, total_pnl: float, daily_pnl: float):
        """Update account-level financial metrics."""
        EQUITY_TOTAL.set(equity)
        PNL_TOTAL.set(total_pnl)
        PNL_DAILY.set(daily_pnl)

    def update_positions(self, count: int):
        """Update active position count."""
        POSITIONS_ACTIVE.set(count)

    def record_order(self, symbol: str, side: str, order_type: str):
        """Increment order counter."""
        ORDERS_TOTAL.labels(symbol=symbol, side=side, type=order_type).inc()

    def record_trade(self, symbol: str, side: str):
        """Increment trade counter."""
        TRADES_TOTAL.labels(symbol=symbol, side=side).inc()

    def update_ai_metrics(self, symbol: str, confidence: float, sentiment: float):
        """Update AI and sentiment scores."""
        AI_CONFIDENCE.labels(symbol=symbol).set(confidence)
        SENTIMENT_SCORE.labels(symbol=symbol).set(sentiment)

# Global instance
metrics_exporter = MetricsExporter()
