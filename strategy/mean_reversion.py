"""
Mean Reversion Strategy based on Z-Score.
Identifies overextended price movements and bets on a return to the mean.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Union
from loguru import logger

from core.base_strategy import BaseStrategy, Signal, OrderSide, Position
from signals.technical import TechnicalIndicators

class MeanReversionStrategy(BaseStrategy):
    """
    Strategy that enters trades when price Z-Score is extreme.
    """

    def __init__(
        self,
        name: str = "MeanReversionStrategy",
        z_threshold: float = 2.0,
        sma_period: int = 20,
        symbol_params: Optional[Dict[str, Dict]] = None
    ):
        super().__init__(name)
        self.z_threshold = z_threshold
        self.sma_period = sma_period
        self.indicators = TechnicalIndicators()
        self.symbol_params = symbol_params or {}

    def _calculate_z_score(self, data: pd.DataFrame) -> float:
        """Calculate Z-Score of current price relative to SMA."""
        if len(data) < self.sma_period:
            return 0.0
            
        close = data['close']
        sma = close.rolling(window=self.sma_period).mean()
        std = close.rolling(window=self.sma_period).std()
        
        last_close = close.iloc[-1]
        last_sma = sma.iloc[-1]
        last_std = std.iloc[-1]
        
        if last_std == 0: return 0.0
        
        return (last_close - last_sma) / last_std

    def analyze(self, data: Union[pd.DataFrame, Dict[str, pd.DataFrame]]) -> Optional[Signal]:
        """
        Analyze price deviation and return signals.
        """
        try:
            # Handle MTF or single DF
            if isinstance(data, dict):
                # Use the lowest timeframe for mean reversion (usually more opportunities)
                available_tfs = sorted(data.keys())
                df = data[available_tfs[0]]
            else:
                df = data

            symbol = df.get("symbol", "UNKNOWN")
            if isinstance(symbol, pd.Series): symbol = symbol.iloc[0]

            # 1. Calculate Z-Score
            z_score = self._calculate_z_score(df)
            
            side = None
            strength = 0.0
            
            # 2. Logic: Buy if price is significantly below mean, Sell if significantly above
            if z_score < -self.z_threshold:
                side = OrderSide.BUY
                strength = min(abs(z_score) / 4.0, 1.0)
                logger.info(f"Mean Reversion BUY Signal for {symbol}: Z={z_score:.2f}")
            elif z_score > self.z_threshold:
                side = OrderSide.SELL
                strength = min(abs(z_score) / 4.0, 1.0)
                logger.info(f"Mean Reversion SELL Signal for {symbol}: Z={z_score:.2f}")

            if side:
                signal = Signal(
                    symbol=symbol,
                    side=side,
                    strength=strength,
                    indicators={
                        "z_score": z_score,
                        "sma_period": self.sma_period,
                        "close": df['close'].iloc[-1]
                    }
                )
                self.record_latest_signal(symbol, signal)
                return signal
                
            return None

        except Exception as e:
            logger.error(f"Error in MeanReversion analysis: {e}")
            return None

    def should_enter(self, signal: Signal, current_price: float, account_balance: float) -> bool:
        """Threshold check for entry."""
        return signal.strength > 0.4

    def should_exit(self, position: Position, current_price: float, data: pd.DataFrame) -> bool:
        """Exit when price returns to the mean (Z-Score near 0)."""
        z_score = self._calculate_z_score(data)
        
        # Exit if Z-score crosses 0 or flips sign
        if position.side == OrderSide.BUY and z_score >= -0.1:
            logger.info(f"Mean Reversion EXIT (Long): Price returned to mean (Z={z_score:.2f})")
            return True
        elif position.side == OrderSide.SELL and z_score <= 0.1:
            logger.info(f"Mean Reversion EXIT (Short): Price returned to mean (Z={z_score:.2f})")
            return True
            
        return False
