"""
Live trading coordinator that integrates all system components.
"""

import asyncio
from typing import Any, Optional
from datetime import datetime
from loguru import logger

from config.config import config
from data.alpha_vantage_feed import AlphaVantageFeed
from data.factory import create_market_data_feed
from data.newsapi_feed import NewsAPIFeed
from signals.sentiment import SentimentAnalyzer
from core.base_strategy import BaseStrategy
from execution.paper_broker import PaperBroker
from execution.order_manager import OrderManager
from analysis.correlation import CorrelationEngine
from risk.position_sizer import PositionSizer
from risk.stop_loss import StopLossManager
from risk.circuit_breaker import CircuitBreaker
from monitoring.pnl_tracker import PnLTracker
from monitoring.alerts import AlertManager, AlertType, AlertLevel, console_handler
from monitoring.telegram_notifier import TelegramNotifier
from monitoring.dashboard_data import DashboardData
from analysis.metrics import metrics_exporter


class LiveTrader:
    """
    Coordinates live trading with full monitoring.

    Features:
    - Automated trading loop
    - Real-time monitoring
    - Alert notifications
    - Dashboard updates
    - PnL tracking
    - Risk management
    """

    SYMBOL_ALIASES = {
        "BTC": ("bitcoin", "btc"),
        "ETH": ("ethereum", "eth"),
        "SOL": ("solana", "sol"),
        "XRP": ("ripple", "xrp"),
        "ADA": ("cardano", "ada"),
    }

    def __init__(
        self,
        feed: Any,
        broker: PaperBroker,
        strategy: BaseStrategy,
        position_sizer: PositionSizer,
        stop_loss_manager: StopLossManager,
        circuit_breaker: CircuitBreaker,
        symbols: list = None,
        update_interval: int = 60,  # seconds
        enable_telegram: bool = False,
        context_refresh_interval: int = 1800,
        web_dashboard: Optional[Any] = None,
    ):
        self.feed = feed
        self.broker = broker
        self.strategy = strategy
        self.position_sizer = position_sizer
        self.stop_loss_manager = stop_loss_manager
        self.circuit_breaker = circuit_breaker
        self.symbols = symbols or ["BTCUSD"]
        self.update_interval = update_interval
        self.context_refresh_interval = context_refresh_interval
        self.running = False
        self.paused = False
        self.last_context_update: Optional[datetime] = None
        self.news_feed = NewsAPIFeed() if config.NEWS_DATA_PROVIDER == "newsapi" else None
        self.fx_feed = AlphaVantageFeed() if config.FOREX_DATA_PROVIDER == "alpha_vantage" else None
        self.web_dashboard = web_dashboard
        self.correlation_engine = CorrelationEngine(lookback_days=30)

        # Initialize monitoring components
        # Use repositories if available from broker
        perf_repo = getattr(broker, 'perf_repo', None)
        self.pnl_tracker = PnLTracker(
            broker.initial_balance, 
            performance_repository=perf_repo,
            web_dashboard=web_dashboard
        )
        self.alert_manager = AlertManager()
        self.alert_manager.add_handler(console_handler)

        # Initialize Telegram if enabled
        self.telegram_notifier = None
        if enable_telegram:
            self.telegram_notifier = TelegramNotifier()
            if self.telegram_notifier.enabled:
                self.alert_manager.add_handler(self.telegram_notifier.create_alert_handler())

        # Initialize order manager
        pos_repo = getattr(broker, 'pos_repo', None)
        self.order_manager = OrderManager(
            broker=broker,
            strategy=strategy,
            position_sizer=position_sizer,
            stop_loss_manager=stop_loss_manager,
            circuit_breaker=circuit_breaker,
            position_repository=pos_repo,
            correlation_engine=self.correlation_engine
        )

        # Initialize dashboard
        self.dashboard = DashboardData(
            pnl_tracker=self.pnl_tracker,
            alert_manager=self.alert_manager,
            broker=broker,
            strategy=strategy,
            circuit_breaker=circuit_breaker
        )

        logger.info(f"LiveTrader initialized for symbols: {self.symbols}")

    async def start(self):
        """Start live trading."""
        if self.running:
            logger.warning("LiveTrader already running")
            return

        self.running = True
        logger.info("🚀 LiveTrader starting...")

        # Start metrics exporter (Phase 5.3)
        metrics_exporter.start()

        # Send start notification
        self.alert_manager.send_alert(
            alert_type=AlertType.SYSTEM_ERROR,
            level=AlertLevel.INFO,
            message="Trading bot started",
            data={"symbols": self.symbols}
        )

        try:
            await self._trading_loop()
        except Exception as e:
            logger.error(f"Error in trading loop: {e}")
            self.alert_manager.system_error(str(e))
            raise
        finally:
            self.running = False
            logger.info("LiveTrader stopped")

    async def stop(self):
        """Stop live trading."""
        logger.info("Stopping LiveTrader...")
        self.running = False

        # Close all positions
        await self.order_manager.close_all_positions()

        # Send stop notification
        self.alert_manager.send_alert(
            alert_type=AlertType.SYSTEM_ERROR,
            level=AlertLevel.INFO,
            message="Trading bot stopped",
            data={}
        )

        await self._close_context_feeds()

    async def _close_context_feeds(self):
        """Close external sentiment and FX adapters."""
        if self.fx_feed:
            await self.fx_feed.close()
            self.fx_feed = None
        if self.news_feed:
            await self.news_feed.close()
            self.news_feed = None

    def _extract_base_symbol(self, symbol: str) -> str:
        """Extract the base asset from a symbol like BTCUSD or ETH/USDT."""
        clean_symbol = symbol.strip().upper().replace("-", "").replace("_", "").replace("/", "")
        for quote in ("USDT", "USDC", "USD", "EUR", "INR", "BTC", "ETH"):
            if clean_symbol.endswith(quote) and len(clean_symbol) > len(quote):
                return clean_symbol[:-len(quote)]
        return clean_symbol

    async def _refresh_market_context(self):
        """Refresh shared market context from FX and news providers."""
        headlines = []
        sentiment_articles = []
        eurusd_rate = None
        forex_status = "disabled"
        news_status = "disabled"

        if self.fx_feed:
            eurusd = await self.fx_feed.get_exchange_rate("EUR/USD")
            eurusd_rate = eurusd.get("exchange_rate") if eurusd else None
            forex_status = "ok" if eurusd_rate else "degraded"

            av_articles = await self.fx_feed.get_news_sentiment(
                topics=["blockchain", "financial_markets"],
                limit=10,
            )
            if av_articles:
                news_status = "ok"
                sentiment_articles.extend(av_articles)
                headlines.extend(article.get("title", "") for article in av_articles[:3])

        if self.news_feed:
            query_terms = []
            for symbol in self.symbols:
                base = self._extract_base_symbol(symbol)
                query_terms.extend(self.SYMBOL_ALIASES.get(base, (base.lower(),)))
            query = " OR ".join(dict.fromkeys(query_terms)) if query_terms else "bitcoin OR forex OR markets"

            newsapi_articles = await self.news_feed.search_market_news(query=query, page_size=10)
            if newsapi_articles:
                news_status = "ok" if news_status != "degraded" else "partial"
                sentiment_articles.extend(newsapi_articles)
                headlines.extend(article.get("title", "") for article in newsapi_articles[:3])
            elif news_status == "disabled":
                news_status = "degraded"

        overall_sentiment = SentimentAnalyzer.score_articles(sentiment_articles)
        headlines = [headline for headline in headlines if headline][:5]

        # AI Reasoning (Phase 1.2)
        from ai.news_reasoner import news_reasoner
        llm_analysis = await news_reasoner.analyze_news(headlines)
        
        # Merge keyword and LLM sentiment (70/30 weight)
        if llm_analysis.get("reason") != "LLM Reasoning disabled or no headlines":
            combined_score = (overall_sentiment["score"] * 0.7) + (float(llm_analysis["score"]) * 0.3)
            final_label = llm_analysis["label"] if abs(llm_analysis["score"]) > abs(overall_sentiment["score"]) else overall_sentiment["label"]
        else:
            combined_score = overall_sentiment["score"]
            final_label = overall_sentiment["label"]

        for symbol in self.symbols:
            self.strategy.update_market_context(symbol, {
                "symbol": symbol,
                "sentiment_score": combined_score,
                "sentiment_label": final_label,
                "article_count": overall_sentiment["article_count"],
                "sentiment_analyzer": "llm_hybrid" if config.LOCAL_LLM_ENABLED else "rule_based",
                "sentiment_model": config.LOCAL_LLM_MODEL,
                "sentiment_reason": llm_analysis.get("reason", ""),
                "eurusd_rate": eurusd_rate,
                "forex_provider": config.FOREX_DATA_PROVIDER,
                "news_provider": config.NEWS_DATA_PROVIDER,
                "forex_status": forex_status,
                "news_status": news_status,
                "headlines": headlines,
                "last_updated": datetime.now(),
            })

        # Update Correlation Matrix
        logger.info("Updating correlation matrix...")
        historical_data = {}
        for symbol in self.symbols:
            candles = await self.feed.get_candlesticks(symbol, timeframe="1h", limit=100)
            if not candles.empty:
                historical_data[symbol] = candles
        
        self.correlation_engine.update_matrix(historical_data)

        self.last_context_update = datetime.now()
        logger.info(
            "Market context updated: sentiment={} ({:.2f}) via {}, EUR/USD={}",
            overall_sentiment["label"],
            overall_sentiment["score"],
            overall_sentiment.get("model") or overall_sentiment.get("analyzer", "rule_based"),
            eurusd_rate,
        )

    async def _trading_loop(self):
        """Main trading loop."""
        iteration = 0

        while self.running:
            try:
                iteration += 1
                logger.info(f"\n{'='*60}")
                logger.info(f"Trading Loop Iteration #{iteration}")
                logger.info(f"{'='*60}")

                if self.paused:
                    logger.info("Bot is PAUSED. Skipping analysis and trading.")
                    # Still update dashboard/PnL but don't check signals
                    self.dashboard.print_dashboard()
                    await asyncio.sleep(self.update_interval)
                    continue

                # 0. Connection Watchdog (Hardening)
                if not await self._check_connections():
                    logger.warning("Connectivity issues detected. Attempting to reconnect...")
                    await self.broker.connect()
                    await self.feed.connect()
                    # Wait a bit before retrying
                    await asyncio.sleep(10)
                    continue

                if (
                    self.last_context_update is None or
                    (datetime.now() - self.last_context_update).total_seconds() >= self.context_refresh_interval
                ):
                    await self._refresh_market_context()

                # 1. Fetch market data for all symbols (Multi-Timeframe)
                market_data_mtf = {} # symbol -> {tf: df}
                primary_tf_data = {} # symbol -> df (for backwards compat where needed)
                
                timeframes = ["5m", "1h", "1D"]
                
                for symbol in self.symbols:
                    market_data_mtf[symbol] = {}
                    for tf in timeframes:
                        candles = await self.feed.get_candlesticks(symbol, timeframe=tf, limit=100)
                        if not candles.empty:
                            candles = candles.copy()
                            candles["symbol"] = symbol
                            market_data_mtf[symbol][tf] = candles
                            
                            # Keep 5m as primary for price updates and simple logic
                            if tf == "5m":
                                primary_tf_data[symbol] = candles
                                current_price = candles['close'].iloc[-1]
                                await self.broker.update_price(symbol, current_price)
                                logger.info(f"Fetched {symbol} ({tf}): ${current_price:,.2f}")

                # 2. Check exits for open positions
                await self.order_manager.check_exits(primary_tf_data)

                # 3. Generate new signals and process
                for symbol, tfs_dict in market_data_mtf.items():
                    if not tfs_dict: continue
                    
                    # ALL timeframes passed to strategy
                    signal = self.strategy.analyze(tfs_dict)

                    # Record AI/Sentiment metrics even if no signal (continuous tracking)
                    if tfs_dict:
                        context = self.strategy.get_market_context(symbol)
                        latest_sig = self.strategy.get_latest_signal(symbol)
                        metrics_exporter.update_ai_metrics(
                            symbol=symbol,
                            confidence=latest_sig.indicators.get('ai_score', 0.5) if latest_sig else 0.5,
                            sentiment=context.get('sentiment_score', 0.0)
                        )

                    if signal:
                        current_price = tfs_dict["5m"]['close'].iloc[-1] if "5m" in tfs_dict else 0
                        if current_price == 0: continue
                        
                        logger.info(
                            "Signal generated for {}: {} (strength: {:.2f}, sentiment: {} {:.2f}, MTF Bias: {:.2f})",
                            symbol,
                            signal.side.value,
                            signal.strength,
                            signal.indicators.get("sentiment_label", "NEUTRAL"),
                            signal.indicators.get("sentiment_score", 0.0),
                            signal.indicators.get("mtf_bias", 0.0),
                        )

                        # Process signal through order manager
                        order = await self.order_manager.process_signal(signal, current_price)

                        if order and order.is_filled():
                            open_positions = self.strategy.get_open_positions(order.symbol)
                            if open_positions:
                                latest_position = open_positions[-1]
                                self.alert_manager.position_opened(
                                    symbol=latest_position.symbol,
                                    side=latest_position.side.value,
                                    size=latest_position.size,
                                    entry_price=latest_position.entry_price,
                                    stop_loss=latest_position.stop_loss or 0.0,
                                    take_profit=latest_position.take_profit or 0.0,
                                )
                            # Send alerts
                            self.alert_manager.trade_executed(
                                symbol=order.symbol,
                                side=order.side.value,
                                quantity=order.quantity,
                                price=order.average_fill_price
                            )
                            # Record metric
                            metrics_exporter.record_trade(order.symbol, order.side.value)

                # 4. Update PnL tracking
                account_balance = await self.broker.get_account_balance()
                positions = self.strategy.get_open_positions()

                position_value = 0.0
                unrealized_pnl = 0.0

                for pos in positions:
                    current_price = await self.broker.get_current_price(pos.symbol)
                    if current_price > 0:
                        position_value += pos.size * current_price
                        unrealized_pnl += pos.calculate_pnl(current_price)

                # Calculate realized PnL
                realized_pnl = sum(t.pnl for t in self.broker.get_all_trades())

                self.pnl_tracker.record_snapshot(
                    account_balance=account_balance,
                    position_value=position_value,
                    unrealized_pnl=unrealized_pnl,
                    realized_pnl_since_start=realized_pnl
                )

                # Update Prometheus Financials
                pnl_summary = self.pnl_tracker.get_summary()
                metrics_exporter.update_financials(
                    equity=account_balance + unrealized_pnl,
                    total_pnl=realized_pnl + unrealized_pnl,
                    daily_pnl=pnl_summary.get('daily_pnl', 0.0)
                )
                metrics_exporter.update_positions(len(positions))

                # 5. Print dashboard
                self.dashboard.print_dashboard()

                # 6. Check risk thresholds
                pnl_summary = self.pnl_tracker.get_summary()

                # Low balance alert
                if account_balance < self.alert_manager.low_balance_threshold:
                    self.alert_manager.low_balance(account_balance, self.alert_manager.low_balance_threshold)

                # Large daily loss alert
                if pnl_summary['daily_pnl'] < -1000:
                    logger.warning(f"Large daily loss detected: ${pnl_summary['daily_pnl']:.2f}")

                # 7. Wait for next iteration
                logger.info(f"\nSleeping for {self.update_interval} seconds...")
                await asyncio.sleep(self.update_interval)

            except asyncio.CancelledError:
                logger.info("Trading loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in trading loop iteration: {e}")
                self.alert_manager.system_error(str(e))
                # Continue running unless it's a critical error
                await asyncio.sleep(self.update_interval)

    async def _check_connections(self) -> bool:
        """Check if all necessary connections are active."""
        try:
            # Check Broker
            if hasattr(self.broker, 'logged_in'):
                if not self.broker.logged_in: return False
            
            # Check Feed (optional connect check)
            # If it's a REST feed, we might skip this or do a ping
            
            # Check Redis
            from data.redis_manager import redis_manager
            if not redis_manager.is_available():
                logger.debug("Redis disconnected, but continuing in degraded mode")
            
            return True
        except Exception as e:
            logger.error(f"Error checking connections: {e}")
            return False

    async def send_daily_summary(self):
        """Send daily trading summary."""
        pnl_summary = self.pnl_tracker.get_summary()
        perf_metrics = self.dashboard.get_performance_metrics()

        if self.telegram_notifier and self.telegram_notifier.enabled:
            await self.telegram_notifier.send_daily_summary(
                total_pnl=pnl_summary['total_return'],
                daily_pnl=pnl_summary['daily_pnl'],
                trades_today=self.circuit_breaker.daily_trades,
                win_rate=perf_metrics['win_rate'],
                account_balance=pnl_summary['current_equity']
            )

        logger.info("Daily summary sent")


# Example usage
async def main():
    logger.info("Starting Live Trading Demo")

    # Initialize components
    feed = create_market_data_feed()
    broker = PaperBroker(initial_balance=10000.0)
    await broker.connect()

    from strategy.signal_strategy import TechnicalSignalStrategy
    from risk.position_sizer import PositionSizer, SizingMethod
    from risk.stop_loss import StopLossManager, StopLossType
    from risk.circuit_breaker import CircuitBreaker

    strategy = TechnicalSignalStrategy()
    position_sizer = PositionSizer(method=SizingMethod.RISK_BASED, risk_per_trade=0.02)
    stop_loss_manager = StopLossManager(stop_loss_type=StopLossType.FIXED_PERCENT)
    circuit_breaker = CircuitBreaker()

    # Create live trader
    trader = LiveTrader(
        feed=feed,
        broker=broker,
        strategy=strategy,
        position_sizer=position_sizer,
        stop_loss_manager=stop_loss_manager,
        circuit_breaker=circuit_breaker,
        symbols=["BTCUSD"],
        update_interval=60,  # 1 minute
        enable_telegram=False
    )

    # Run for a few iterations (in production, this would run indefinitely)
    try:
        # Start trading
        task = asyncio.create_task(trader.start())

        # Run for 5 minutes (5 iterations)
        await asyncio.sleep(300)

        # Stop trading
        await trader.stop()
        await task

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        await trader.stop()

    finally:
        await feed.close()
        await broker.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
