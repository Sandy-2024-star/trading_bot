"""
Telegram notification system for trading alerts.
"""

import asyncio
import httpx
from typing import Optional
from loguru import logger

from monitoring.alerts import Alert, AlertLevel, AlertType
from config.config import config


class TelegramNotifier:
    """
    Sends trading alerts to Telegram.

    Features:
    - Async message sending
    - Rich text formatting (Markdown)
    - Alert filtering by level
    - Rate limiting to avoid spam
    """

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
        min_level: AlertLevel = AlertLevel.INFO
    ):
        self.bot_token = bot_token or config.TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or config.TELEGRAM_CHAT_ID
        self.min_level = min_level
        self.enabled = bool(self.bot_token and self.chat_id)

        if not self.enabled:
            logger.warning("Telegram notifications disabled: bot_token or chat_id not configured")
        else:
            logger.info(f"TelegramNotifier initialized for chat_id: {self.chat_id}")

    async def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """
        Send a message to Telegram.

        Args:
            text: Message text
            parse_mode: Formatting mode (Markdown or HTML)

        Returns:
            True if sent successfully
        """
        if not self.enabled:
            logger.debug("Telegram not configured, message not sent")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                logger.debug(f"Telegram message sent successfully")
                return True

        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    async def send_alert(self, alert: Alert):
        """
        Send an alert to Telegram.

        Args:
            alert: Alert object
        """
        # Check alert level
        level_priority = {
            AlertLevel.INFO: 0,
            AlertLevel.WARNING: 1,
            AlertLevel.ERROR: 2,
            AlertLevel.CRITICAL: 3
        }

        if level_priority[alert.level] < level_priority[self.min_level]:
            return

        # Format message
        message = self._format_alert(alert)

        # Send message
        await self.send_message(message)

    def _format_alert(self, alert: Alert) -> str:
        """
        Format an alert for Telegram.

        Args:
            alert: Alert object

        Returns:
            Formatted message string
        """
        # Emoji for alert level
        level_emoji = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.ERROR: "❌",
            AlertLevel.CRITICAL: "🚨"
        }

        emoji = level_emoji.get(alert.level, "")
        timestamp = alert.timestamp.strftime("%Y-%m-%d %H:%M:%S")

        # Build message
        message = f"{emoji} *{alert.level.value.upper()}*\n"
        message += f"_{timestamp}_\n\n"
        message += f"{alert.message}\n"

        # Add data if available
        if alert.data:
            message += "\n*Details:*\n"
            for key, value in alert.data.items():
                if key not in ['symbol', 'side']:  # Already in message usually
                    if isinstance(value, float):
                        if key.endswith('_pct') or 'percent' in key.lower():
                            message += f"• {key.replace('_', ' ').title()}: {value:.2f}%\n"
                        elif 'price' in key.lower() or 'pnl' in key.lower() or 'balance' in key.lower():
                            message += f"• {key.replace('_', ' ').title()}: ${value:,.2f}\n"
                        else:
                            message += f"• {key.replace('_', ' ').title()}: {value:.4f}\n"
                    else:
                        message += f"• {key.replace('_', ' ').title()}: {value}\n"

        return message

    async def send_daily_summary(
        self,
        total_pnl: float,
        daily_pnl: float,
        trades_today: int,
        win_rate: float,
        account_balance: float
    ):
        """
        Send daily trading summary.

        Args:
            total_pnl: Total PnL
            daily_pnl: Today's PnL
            trades_today: Number of trades today
            win_rate: Win rate percentage
            account_balance: Current account balance
        """
        message = "📊 *Daily Trading Summary*\n\n"
        message += f"💰 Account Balance: ${account_balance:,.2f}\n"
        message += f"📈 Total PnL: ${total_pnl:,.2f}\n"
        message += f"📅 Today's PnL: ${daily_pnl:,.2f}\n"
        message += f"🔢 Trades Today: {trades_today}\n"
        message += f"✅ Win Rate: {win_rate:.1f}%\n"

        await self.send_message(message)

    async def send_position_update(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        current_price: float,
        unrealized_pnl: float,
        unrealized_pnl_pct: float
    ):
        """
        Send open position update.

        Args:
            symbol: Trading symbol
            side: Position side (BUY/SELL)
            entry_price: Entry price
            current_price: Current market price
            unrealized_pnl: Unrealized PnL
            unrealized_pnl_pct: Unrealized PnL percentage
        """
        emoji = "📈" if unrealized_pnl > 0 else "📉"
        message = f"{emoji} *Position Update: {symbol}*\n\n"
        message += f"Side: {side.upper()}\n"
        message += f"Entry Price: ${entry_price:,.2f}\n"
        message += f"Current Price: ${current_price:,.2f}\n"
        message += f"Unrealized PnL: ${unrealized_pnl:,.2f} ({unrealized_pnl_pct:+.2f}%)\n"

        await self.send_message(message)

    async def send_system_status(
        self,
        status: str,
        uptime: str,
        circuit_breaker_state: str,
        open_positions: int
    ):
        """
        Send system status update.

        Args:
            status: System status (running/stopped/error)
            uptime: System uptime string
            circuit_breaker_state: Circuit breaker state
            open_positions: Number of open positions
        """
        status_emoji = {
            "running": "✅",
            "stopped": "⏸️",
            "error": "❌"
        }

        emoji = status_emoji.get(status.lower(), "ℹ️")
        message = f"{emoji} *System Status*\n\n"
        message += f"Status: {status.upper()}\n"
        message += f"Uptime: {uptime}\n"
        message += f"Circuit Breaker: {circuit_breaker_state}\n"
        message += f"Open Positions: {open_positions}\n"

        await self.send_message(message)

    def create_alert_handler(self):
        """
        Create an alert handler function for AlertManager.

        Returns:
            Handler function that can be added to AlertManager
        """
        def handler(alert: Alert):
            """Handle alert by sending to Telegram."""
            # Run async in event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is already running, create a task
                    loop.create_task(self.send_alert(alert))
                else:
                    # Otherwise run it
                    loop.run_until_complete(self.send_alert(alert))
            except Exception as e:
                logger.error(f"Error sending alert to Telegram: {e}")

        return handler


# Example usage
async def main():
    # Note: You need to set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in config
    notifier = TelegramNotifier(
        bot_token="YOUR_BOT_TOKEN",  # Get from @BotFather
        chat_id="YOUR_CHAT_ID",      # Your Telegram chat ID
        min_level=AlertLevel.INFO
    )

    # Send a simple message
    await notifier.send_message("🤖 Trading bot started!")

    # Send daily summary
    await notifier.send_daily_summary(
        total_pnl=1250.50,
        daily_pnl=150.25,
        trades_today=5,
        win_rate=60.0,
        account_balance=11250.50
    )

    # Send position update
    await notifier.send_position_update(
        symbol="BTCUSD",
        side="BUY",
        entry_price=50000.0,
        current_price=51000.0,
        unrealized_pnl=100.0,
        unrealized_pnl_pct=2.0
    )

    # Send system status
    await notifier.send_system_status(
        status="running",
        uptime="2h 15m",
        circuit_breaker_state="CLOSED",
        open_positions=2
    )


if __name__ == "__main__":
    asyncio.run(main())
