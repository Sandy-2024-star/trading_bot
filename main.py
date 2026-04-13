"""
Main entry point for the trading bot.
Demonstrates all 4 phases of functionality.
Phase 1: Data ingestion + signal generation
Phase 2: Strategy + risk management
Phase 3: Broker execution + backtesting
Phase 4: Monitoring + live trading
"""

import asyncio
import socket
from loguru import logger
from data.alpha_vantage_feed import AlphaVantageFeed
from data.factory import create_market_data_feed
from data.newsapi_feed import NewsAPIFeed
from signals.sentiment import SentimentAnalyzer
from signals.technical import TechnicalIndicators
from strategy.signal_strategy import TechnicalSignalStrategy
from strategy.factory import create_strategy
from core.base_strategy import Position, OrderSide
from risk.position_sizer import PositionSizer, SizingMethod
from risk.stop_loss import StopLossManager, StopLossType
from risk.circuit_breaker import CircuitBreaker, RiskManager
from execution.backtester import Backtester
from execution.performance import PerformanceAnalyzer
from execution.paper_broker import PaperBroker
from execution.mt5_broker import MT5Broker
from monitoring.live_trader import LiveTrader
from monitoring.web_dashboard import WebDashboard
from monitoring.dashboard_data import DashboardData
from config.config import config


def find_available_port(start_port: int = 8000, attempts: int = 10) -> int:
    """Return the first available localhost port from a small candidate range."""
    for port in range(start_port, start_port + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("0.0.0.0", 0))
        return sock.getsockname()[1]


async def demo_phase1():
    """
    Demo Phase 1: Fetch crypto data and generate trading signals.
    """
    logger.info("=== Trading Bot Phase 1 Demo ===")
    logger.info(f"Environment: {config.ENVIRONMENT}")

    # Validate configuration
    config.validate()

    # Initialize data feed
    feed = create_market_data_feed()

    try:
        # 1. Fetch real-time ticker
        logger.info("\n[1] Fetching real-time ticker for BTCUSD...")
        ticker = await feed.get_ticker("BTCUSD")
        if ticker:
            logger.info(f"BTC Price: ${ticker['last_price']:,.2f}")
            logger.info(f"24h Volume: ${ticker['volume_24h']:,.0f}")
            logger.info(f"24h High: ${ticker['high_24h']:,.2f}")
            logger.info(f"24h Low: ${ticker['low_24h']:,.2f}")

        # 2. Fetch orderbook
        logger.info("\n[2] Fetching orderbook depth...")
        orderbook = await feed.get_orderbook("BTCUSD", depth=5)
        if orderbook:
            logger.info(f"Top 3 Bids: {orderbook['bids'][:3]}")
            logger.info(f"Top 3 Asks: {orderbook['asks'][:3]}")
        else:
            logger.info("Orderbook data not available from the configured provider")

        # 3. Fetch historical candlesticks
        logger.info("\n[3] Fetching 1-hour candlesticks (last 100)...")
        candles = await feed.get_candlesticks("BTCUSD", timeframe="1h", limit=100)

        if not candles.empty:
            logger.info(f"Fetched {len(candles)} candles")
            logger.info(
                f"\nMost recent candles:\n{candles[['timestamp', 'open', 'high', 'low', 'close', 'volume']].tail()}"
            )

            # 4. Generate technical signals
            logger.info("\n[4] Generating trading signals...")
            indicators = TechnicalIndicators()
            signals_df = indicators.generate_signals(candles)

            # Display results
            latest = signals_df.iloc[-1]
            logger.info(f"\n=== TRADING SIGNAL ===")
            logger.info(f"Signal: {latest['signal']}")
            logger.info(f"Signal Score: {latest['signal_score']:.2f}")
            logger.info(f"RSI: {latest['rsi']:.2f}")
            logger.info(f"MACD: {latest['macd']:.2f}")
            logger.info(f"MACD Signal: {latest['macd_signal']:.2f}")
            logger.info(f"MACD Histogram: {latest['macd_hist']:.2f}")
            logger.info(f"Bollinger Upper: ${latest['bb_upper']:.2f}")
            logger.info(f"Bollinger Middle: ${latest['bb_middle']:.2f}")
            logger.info(f"Bollinger Lower: ${latest['bb_lower']:.2f}")
            logger.info(f"SMA(20): ${latest['sma_20']:.2f}")
            logger.info(f"SMA(50): ${latest['sma_50']:.2f}")

            # Signal interpretation
            logger.info(f"\n=== INTERPRETATION ===")
            if latest["rsi"] < 30:
                logger.info("⚠️  RSI indicates OVERSOLD condition (potential buy)")
            elif latest["rsi"] > 70:
                logger.info("⚠️  RSI indicates OVERBOUGHT condition (potential sell)")
            else:
                logger.info(f"✓ RSI in neutral zone ({latest['rsi']:.1f})")

            if latest["close"] < latest["bb_lower"]:
                logger.info("⚠️  Price below lower Bollinger Band (potential buy)")
            elif latest["close"] > latest["bb_upper"]:
                logger.info("⚠️  Price above upper Bollinger Band (potential sell)")
            else:
                logger.info("✓ Price within Bollinger Bands")

            if latest["macd_hist"] > 0:
                logger.info("✓ MACD histogram positive (bullish momentum)")
            else:
                logger.info("⚠️  MACD histogram negative (bearish momentum)")

        # 5. Multi-symbol fetch demo
        logger.info("\n[5] Fetching multiple symbols...")
        symbols = ["BTCUSD", "ETHUSD", "SOLUSD"]
        tickers = await feed.get_multiple_tickers(symbols)
        for t in tickers:
            logger.info(f"{t['symbol']}: ${t['last_price']:,.2f}")

    except Exception as e:
        logger.error(f"Error in demo: {e}")

    finally:
        await feed.close()
        logger.info("\n=== Demo Complete ===")


async def demo_phase2():
    """
    Demo Phase 2: Strategy execution + risk management.
    """
    logger.info("=== Trading Bot Phase 2 Demo ===")
    logger.info(f"Environment: {config.ENVIRONMENT}")

    # Initialize components
    feed = create_market_data_feed()
    strategy = create_strategy(name="DemoStrategy")

    # Risk management components
    position_sizer = PositionSizer(
        method=SizingMethod.RISK_BASED,
        risk_per_trade=0.02,
        max_position_size=5000,
        min_position_size=100,
    )

    stop_loss_manager = StopLossManager(
        stop_loss_type=StopLossType.FIXED_PERCENT,
        stop_loss_percent=0.05,
        take_profit_percent=0.10,
    )

    circuit_breaker = CircuitBreaker(
        max_daily_loss_percent=0.05,
        max_consecutive_losses=3,
        max_drawdown_percent=0.15,
        max_open_positions=5,
    )

    risk_manager = RiskManager(circuit_breaker)

    # Simulated account
    account_balance = 10000.0

    try:
        logger.info(f"\n=== Account Setup ===")
        logger.info(f"Starting Balance: ${account_balance:,.2f}")

        # 1. Fetch market data
        logger.info("\n[1] Fetching market data for BTCUSD...")
        candles = await feed.get_candlesticks("BTCUSD", timeframe="1h", limit=100)

        if candles.empty:
            logger.error("No market data available")
            return

        current_price = candles["close"].iloc[-1]
        logger.info(f"Current BTC Price: ${current_price:,.2f}")

        # 2. Generate signal
        logger.info("\n[2] Analyzing market and generating signal...")
        signal = strategy.analyze(candles)

        if signal:
            logger.info(f"Signal: {signal}")
            logger.info(f"Side: {signal.side.value}")
            logger.info(f"Strength: {signal.strength:.2f}")
            logger.info(
                f"Indicators: RSI={signal.indicators.get('rsi', 0):.2f}, "
                f"MACD={signal.indicators.get('macd', 0):.2f}"
            )

            # 3. Check risk management
            logger.info("\n[3] Checking risk management...")
            open_positions = strategy.get_open_positions()
            can_trade = risk_manager.can_trade(account_balance, len(open_positions), [])

            logger.info(f"Trading Allowed: {can_trade}")
            logger.info(f"Circuit Breaker Status: {circuit_breaker.get_status()}")

            if not can_trade:
                logger.warning("Trading blocked by circuit breaker")
                return

            # 4. Check entry conditions
            logger.info("\n[4] Evaluating entry conditions...")
            should_enter = strategy.should_enter(signal, current_price, account_balance)
            logger.info(f"Should Enter: {should_enter}")

            if should_enter:
                # 5. Calculate position size
                logger.info("\n[5] Calculating position size...")

                # Calculate stop loss first
                is_long = signal.side == OrderSide.BUY
                stop_loss, take_profit = stop_loss_manager.calculate_both(
                    current_price, is_long
                )

                logger.info(f"Entry Price: ${current_price:.2f}")
                logger.info(f"Stop Loss: ${stop_loss:.2f}")
                logger.info(f"Take Profit: ${take_profit:.2f}")

                # Calculate position size
                position_value = position_sizer.calculate_size(
                    account_balance, current_price, stop_loss, signal.strength
                )

                quantity = position_sizer.calculate_quantity(
                    account_balance, current_price, stop_loss, signal.strength
                )

                logger.info(f"Position Value: ${position_value:,.2f}")
                logger.info(f"Quantity: {quantity:.4f} BTC")

                # Validate position size
                is_valid = position_sizer.validate_size(position_value, account_balance)
                logger.info(f"Position Size Valid: {is_valid}")

                # Calculate risk/reward
                rr_ratio = stop_loss_manager.calculate_risk_reward_ratio(
                    current_price, stop_loss, take_profit, is_long
                )
                logger.info(f"Risk/Reward Ratio: {rr_ratio:.2f}:1")

                if is_valid:
                    # 6. Open position (simulated)
                    logger.info("\n[6] Opening position (simulated)...")
                    position = Position(
                        symbol="BTCUSD",
                        side=signal.side,
                        size=quantity,
                        entry_price=current_price,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                    )
                    strategy.add_position(position)

                    logger.info(f"✓ Position opened: {position}")
                    logger.info(
                        f"Position Value: ${position.size * position.entry_price:,.2f}"
                    )

                    # Update account
                    account_balance -= position_value

                    # 7. Simulate price movement and check exit
                    logger.info("\n[7] Simulating price movement...")

                    # Simulate price going up 3%
                    simulated_price = current_price * 1.03
                    logger.info(f"Simulated Price: ${simulated_price:,.2f} (+3%)")

                    # Calculate PnL
                    pnl = position.calculate_pnl(simulated_price)
                    pnl_percent = position.calculate_pnl_percent(simulated_price)
                    logger.info(f"Unrealized PnL: ${pnl:.2f} ({pnl_percent:.2f}%)")

                    # Check exit conditions
                    should_exit = strategy.should_exit(
                        position, simulated_price, candles
                    )
                    logger.info(f"Should Exit: {should_exit}")

                    if should_exit or simulated_price >= take_profit:
                        # Close position
                        logger.info("\n[8] Closing position...")
                        strategy.close_position(position, simulated_price)
                        account_balance += position_value + pnl

                        # Record trade in circuit breaker
                        risk_manager.record_trade_result(pnl)

                        logger.info(f"✓ Position closed at ${simulated_price:.2f}")
                        logger.info(f"Realized PnL: ${pnl:.2f}")
                        logger.info(f"New Balance: ${account_balance:,.2f}")

        else:
            logger.info("No trading signal generated (HOLD)")

        # 9. Strategy statistics
        logger.info("\n[9] Strategy Statistics")
        stats = strategy.get_stats()
        logger.info(f"Total Trades: {stats['total_trades']}")
        logger.info(f"Winning Trades: {stats['winning_trades']}")
        logger.info(f"Losing Trades: {stats['losing_trades']}")
        logger.info(f"Win Rate: {stats['win_rate']:.1f}%")
        logger.info(f"Total PnL: ${stats['total_pnl']:.2f}")

        # 10. Risk status
        logger.info("\n[10] Risk Management Status")
        risk_status = risk_manager.get_risk_status()
        logger.info(f"Circuit Breaker State: {risk_status['circuit_breaker']['state']}")
        logger.info(f"Trading Allowed: {risk_status['trading_allowed']}")
        logger.info(
            f"Consecutive Losses: {risk_status['circuit_breaker']['consecutive_losses']}"
        )
        logger.info(f"Daily Trades: {risk_status['circuit_breaker']['daily_trades']}")

    except Exception as e:
        logger.error(f"Error in Phase 2 demo: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await feed.close()
        logger.info("\n=== Phase 2 Demo Complete ===")


async def demo_phase3():
    """
    Demo Phase 3: Backtesting on historical data.
    """
    logger.info("=== Trading Bot Phase 3 Demo: Backtesting ===")

    # Initialize data feed
    feed = create_market_data_feed()

    try:
        # 1. Fetch historical data
        logger.info("\n[1] Fetching historical data for backtesting...")
        candles = await feed.get_candlesticks("BTCUSD", timeframe="1h", limit=500)

        if candles.empty:
            logger.error("No historical data available")
            return

        logger.info(f"Fetched {len(candles)} candles")
        logger.info(
            f"Period: {candles['timestamp'].iloc[0]} to {candles['timestamp'].iloc[-1]}"
        )
        logger.info(
            f"Price range: ${candles['close'].min():,.2f} - ${candles['close'].max():,.2f}"
        )

        # 2. Initialize strategy and risk components
        logger.info("\n[2] Initializing strategy and risk management...")
        strategy = create_strategy(name="BacktestStrategy")

        position_sizer = PositionSizer(
            method=SizingMethod.RISK_BASED, risk_per_trade=0.02, max_position_size=5000
        )

        stop_loss_manager = StopLossManager(
            stop_loss_type=StopLossType.FIXED_PERCENT,
            stop_loss_percent=0.05,
            take_profit_percent=0.10,
        )

        circuit_breaker = CircuitBreaker(
            max_daily_loss_percent=0.05, max_consecutive_losses=3
        )

        # 3. Create and run backtester
        logger.info("\n[3] Running backtest...")
        backtester = Backtester(
            strategy=strategy,
            position_sizer=position_sizer,
            stop_loss_manager=stop_loss_manager,
            circuit_breaker=circuit_breaker,
            initial_balance=10000.0,
        )

        result = await backtester.run(data=candles, symbol="BTCUSD", lookback_period=50)

        # 4. Print backtest summary
        logger.info("\n[4] Backtest Results")
        result.print_summary()

        # 5. Detailed performance analysis
        logger.info("[5] Detailed Performance Analysis")
        analyzer = PerformanceAnalyzer(
            trades=result.trades,
            equity_curve=result.equity_curve,
            initial_balance=result.initial_balance,
        )

        analyzer.print_report()

        # 6. Show equity curve
        if not result.equity_curve.empty:
            logger.info("\n[6] Equity Curve (last 10 periods)")
            logger.info(
                result.equity_curve[["timestamp", "equity", "cash", "position_value"]]
                .tail(10)
                .to_string()
            )

        # 7. Show sample trades
        if result.trades:
            logger.info(
                f"\n[7] Sample Trades (showing first 5 of {len(result.trades)})"
            )
            for i, trade in enumerate(result.trades[:5]):
                logger.info(
                    f"  Trade {i + 1}: {trade.side.value.upper()} {trade.quantity:.4f} @ "
                    f"${trade.price:.2f}, PnL: ${trade.pnl:.2f}, Fees: ${trade.fees:.2f}"
                )

    except Exception as e:
        logger.error(f"Error in Phase 3 demo: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await feed.close()
        logger.info("\n=== Phase 3 Demo Complete ===")


async def demo_phase4():
    """
    Demo Phase 4: Live trading with monitoring.
    """
    logger.info("=== Trading Bot Phase 4 Demo: Live Trading with Monitoring ===")

    # Initialize components
    feed = create_market_data_feed()
    broker = PaperBroker(initial_balance=10000.0)
    await broker.connect()

    try:
        logger.info("\n[1] Initializing trading system...")

        strategy = create_strategy(name="LiveDemoStrategy")

        position_sizer = PositionSizer(
            method=SizingMethod.RISK_BASED, risk_per_trade=0.02, max_position_size=3000
        )

        stop_loss_manager = StopLossManager(
            stop_loss_type=StopLossType.FIXED_PERCENT,
            stop_loss_percent=0.05,
            take_profit_percent=0.10,
        )

        circuit_breaker = CircuitBreaker(
            max_daily_loss_percent=0.05, max_consecutive_losses=3
        )

        logger.info("[2] Starting live trading demo...")
        logger.info("    Trading symbols: BTCUSD")
        logger.info("    Update interval: 30 seconds")
        logger.info("    Demo duration: 3 iterations (~90 seconds)")

        # Create live trader
        trader = LiveTrader(
            feed=feed,
            broker=broker,
            strategy=strategy,
            position_sizer=position_sizer,
            stop_loss_manager=stop_loss_manager,
            circuit_breaker=circuit_breaker,
            symbols=["BTCUSD"],
            update_interval=30,  # 30 seconds for demo
            enable_telegram=False,
            context_refresh_interval=1800,
        )

        # Run for 3 iterations (demo mode)
        logger.info("\n[3] Running live trading...")
        task = asyncio.create_task(trader.start())

        # Let it run for 90 seconds (3 iterations)
        await asyncio.sleep(90)

        # Stop trading
        logger.info("\n[4] Stopping trading...")
        await trader.stop()

        try:
            await asyncio.wait_for(task, timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("Trading task did not complete in time")

        # Print final summary
        logger.info("\n[5] Final Summary")
        trader.pnl_tracker.print_summary()

        # Get final dashboard
        logger.info("\n[6] Final Dashboard")
        trader.dashboard.print_dashboard()

        logger.info("\n💡 In production, the live trader would run continuously")
        logger.info("   It can be stopped with Ctrl+C or through system signals")

    except Exception as e:
        logger.error(f"Error in Phase 4 demo: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await broker.disconnect()
        await feed.close()
        logger.info("\n=== Phase 4 Demo Complete ===")


async def demo_sources():
    """
    Demo: Free-source adapters for FX data and news sentiment.
    """
    logger.info("=== Free Sources Demo ===")
    logger.info(f"Forex provider: {config.FOREX_DATA_PROVIDER}")
    logger.info(f"News provider: {config.NEWS_DATA_PROVIDER}")

    fx_feed = AlphaVantageFeed()
    news_feed = NewsAPIFeed()

    try:
        logger.info("\n[1] Fetching EUR/USD exchange rate...")
        eurusd = await fx_feed.get_exchange_rate("EUR/USD")
        if eurusd:
            logger.info(f"EUR/USD: {eurusd['exchange_rate']:.5f}")
        else:
            logger.warning("No EUR/USD data returned. Check ALPHA_VANTAGE_API_KEY.")

        logger.info("\n[2] Fetching Alpha Vantage FX candles...")
        candles = await fx_feed.get_candlesticks("EUR/USD", timeframe="1D", limit=10)
        if not candles.empty:
            logger.info(f"Fetched {len(candles)} FX candles")
            logger.info(candles.tail().to_string())
        else:
            logger.warning(
                "No FX candles returned. Check Alpha Vantage configuration or limits."
            )

        logger.info("\n[3] Fetching NewsAPI articles...")
        articles = await news_feed.search_market_news(
            "bitcoin OR ethereum", page_size=10
        )
        logger.info(f"Fetched {len(articles)} articles")

        logger.info("\n[4] Scoring article sentiment...")
        sentiment = SentimentAnalyzer.score_articles(articles)
        logger.info(
            "Sentiment: {} ({:.2f}) across {} articles via {}",
            sentiment["label"],
            sentiment["score"],
            sentiment["article_count"],
            sentiment.get("model") or sentiment.get("analyzer", "rule_based"),
        )
        if sentiment.get("reason"):
            logger.info("Sentiment reason: {}", sentiment["reason"])

        if articles:
            logger.info("\n[5] Sample headlines")
            for article in articles[:3]:
                logger.info(f"- {article.get('title', 'Untitled article')}")

    except Exception as exc:
        logger.error(f"Error in free sources demo: {exc}")
        import traceback

        traceback.print_exc()

    finally:
        await fx_feed.close()
        await news_feed.close()
        logger.info("\n=== Free Sources Demo Complete ===")


async def demo_web():
    """
    Demo: Web Dashboard with Live Trading.
    Opens a web interface at http://localhost:8000
    """
    logger.info("=== Trading Bot Web Dashboard ===")
    dashboard_port = find_available_port(8000, attempts=20)

    # Initialize DB
    from database import init_db, Session
    from execution.repositories import OrderRepository, TradeRepository
    from monitoring.repositories.performance_repository import PerformanceRepository

    init_db()
    session = Session()

    # Initialize components
    feed = create_market_data_feed()

    # Inject repositories for persistence
    broker = PaperBroker(
        initial_balance=10000.0,
        order_repository=OrderRepository(session),
        trade_repository=TradeRepository(session),
    )
    # Add performance repo manually to broker for PnLTracker discovery
    broker.perf_repo = PerformanceRepository(session)

    await broker.connect()

    try:
        logger.info("\n[1] Initializing trading system with web dashboard...")

        strategy = create_strategy(name="WebDashboardStrategy")

        position_sizer = PositionSizer(
            method=SizingMethod.RISK_BASED, risk_per_trade=0.02, max_position_size=3000
        )

        stop_loss_manager = StopLossManager(
            stop_loss_type=StopLossType.FIXED_PERCENT,
            stop_loss_percent=0.05,
            take_profit_percent=0.10,
        )

        circuit_breaker = CircuitBreaker(
            max_daily_loss_percent=0.05, max_consecutive_losses=3
        )

        # Create dashboard data first (needed for web_dashboard)
        dashboard_data = DashboardData(
            pnl_tracker=None,  # Will be set by LiveTrader
            alert_manager=None,  # Will be set by LiveTrader
            broker=broker,
            strategy=strategy,
            circuit_breaker=circuit_breaker,
        )

        # Create web dashboard instance
        web_dashboard = WebDashboard(
            dashboard_data, host="0.0.0.0", port=dashboard_port
        )

        # Create live trader, passing the dashboard for WebSocket broadcasts
        trader = LiveTrader(
            feed=feed,
            broker=broker,
            strategy=strategy,
            position_sizer=position_sizer,
            stop_loss_manager=stop_loss_manager,
            circuit_breaker=circuit_breaker,
            symbols=["BTCUSD"],
            update_interval=30,
            enable_telegram=False,
            context_refresh_interval=1800,
            web_dashboard=web_dashboard,
        )

        # Link trader's actual monitoring components back to dashboard_data
        dashboard_data.pnl_tracker = trader.pnl_tracker
        dashboard_data.alert_manager = trader.alert_manager

        logger.info("\n[2] Starting web dashboard...")
        logger.info(f"    🌐 Open your browser to: http://localhost:{dashboard_port}")
        logger.info("    Theme options: Light / Dark / System (auto)")
        logger.info("    Dashboard tabs: Demo / Paper Trading | Real Broker Trading")
        logger.info("    Dashboard updates every 3 seconds")
        logger.info("")
        logger.info("💡 Paper trading runs in parallel, updating every 30 seconds")
        logger.info("   Real broker readiness is shown in the second tab")
        logger.info("   Press Ctrl+C to stop everything gracefully")
        logger.info("")

        # Run both web dashboard and live trader concurrently
        await asyncio.gather(web_dashboard.run(), trader.start())

    except KeyboardInterrupt:
        logger.info("\n[3] Stopping gracefully...")
        await trader.stop() if "trader" in locals() else None

    except Exception as e:
        logger.error(f"Error in web dashboard: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await trader.stop() if "trader" in locals() else None
        await broker.disconnect()
        await feed.close()
        logger.info("\n=== Web Dashboard Stopped ===")


async def demo_mt5():
    """
    Demo Phase 5: MT5 Live Trading via MetaApi Cloud.

    Connects to MetaTrader 5 demo account:
    - Account: Sandesh P
    - Server: MetaQuotes-Demo
    - Balance: $100 USD
    """
    logger.info("=== MT5 Live Trading Demo ===")
    logger.info("Account: Sandesh P")
    logger.info("Server: MetaQuotes-Demo")
    logger.info("Balance: $100 USD")

    if not config.METAAPI_TOKEN or not config.METAAPI_ACCOUNT_ID:
        logger.error("METAAPI_TOKEN and METAAPI_ACCOUNT_ID not configured")
        logger.info("Set these in config/.env:")
        logger.info("  METAAPI_TOKEN=your-token")
        logger.info("  METAAPI_ACCOUNT_ID=your-account-id")
        return

    broker = MT5Broker(
        api_token=config.METAAPI_TOKEN, account_id=config.METAAPI_ACCOUNT_ID
    )

    try:
        await broker.connect()

        logger.info("\n[1] Account Info:")
        balance = await broker.get_account_balance()
        logger.info(f"  Balance: ${balance:,.2f}")

        logger.info("\n[2] Forex Prices:")
        for symbol in ["EURUSD", "GBPUSD", "USDJPY"]:
            try:
                price = await broker.get_current_price(symbol)
                logger.info(f"  {symbol}: {price:.5f}")
            except Exception as e:
                logger.warning(f"  {symbol}: Error - {e}")

        logger.info("\n[3] Commodities:")
        for symbol in ["XAUUSD", "XAGUSD"]:
            try:
                price = await broker.get_current_price(symbol)
                logger.info(f"  {symbol}: ${price:.2f}")
            except Exception as e:
                logger.warning(f"  {symbol}: Error - {e}")

        logger.info("\n[4] Open Positions:")
        positions = broker.get_positions_summary()
        if positions:
            for pos in positions:
                logger.info(
                    f"  {pos['symbol']}: {pos['volume']} lots, PnL=${pos['profit']:.2f}"
                )
        else:
            logger.info("  No open positions")

        logger.info("\n[5] MT5 Status:")
        logger.info("  Connection: Active")
        logger.info("  Ready for trading!")

        logger.info("\n=== MT5 Demo Complete ===")
        logger.info("Use MT5Broker in your strategy for live trading")

    except Exception as e:
        logger.error(f"Error in MT5 demo: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await broker.disconnect()


def main():
    """Run the demo."""
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "phase2":
            asyncio.run(demo_phase2())
        elif sys.argv[1] == "phase3" or sys.argv[1] == "backtest":
            asyncio.run(demo_phase3())
        elif sys.argv[1] == "phase4" or sys.argv[1] == "live":
            asyncio.run(demo_phase4())
        elif sys.argv[1] == "sources":
            asyncio.run(demo_sources())
        elif sys.argv[1] == "web" or sys.argv[1] == "dashboard":
            asyncio.run(demo_web())
        elif sys.argv[1] == "mt5":
            asyncio.run(demo_mt5())
        else:
            print(f"Unknown command: {sys.argv[1]}")
            print("Available commands:")
            print("  phase2              - Phase 2 demo")
            print("  phase3 (backtest)   - Phase 3 demo")
            print("  phase4 (live)       - Phase 4 demo")
            print("  sources             - Alpha Vantage + NewsAPI demo")
            print("  web (dashboard)     - Web dashboard")
            print("  mt5                 - MT5 Live Trading demo")
    else:
        asyncio.run(demo_web())


if __name__ == "__main__":
    main()
