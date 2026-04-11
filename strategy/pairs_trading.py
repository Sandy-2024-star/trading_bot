"""
Pairs Trading Strategy (Statistical Arbitrage).
Trades the divergence between two highly correlated assets.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List, Tuple, Union
from loguru import logger
from datetime import datetime
import statsmodels.api as sm

from core.base_strategy import BaseStrategy, Signal, OrderSide, Position

class PairsTradingStrategy(BaseStrategy):
    """
    Implements statistical arbitrage using cointegration and Z-Score.
    """

    def __init__(
        self,
        name: str = "PairsTradingStrategy",
        z_score_entry: float = 2.0,
        z_score_exit: float = 0.5,
        lookback: int = 60
    ):
        super().__init__(name)
        self.z_score_entry = z_score_entry
        self.z_score_exit = z_score_exit
        self.lookback = lookback
        self.symbol_pairs: List[Tuple[str, str]] = [] # List of (Asset A, Asset B)

    def add_pair(self, asset_a: str, asset_b: str):
        """Register a pair to trade."""
        self.symbol_pairs.append((asset_a, asset_b))
        logger.info(f"Registered pair for trading: {asset_a} & {asset_b}")

    def _calculate_z_score(self, series_a: pd.Series, series_b: pd.Series) -> float:
        """
        Calculate the Z-Score of the spread between two series.
        """
        # Linear regression to find hedge ratio
        x = sm.add_constant(series_b)
        model = sm.OLS(series_a, x).fit()
        hedge_ratio = model.params[1]
        
        # Calculate spread
        spread = series_a - (hedge_ratio * series_b)
        
        # Z-Score of spread
        mean = spread.mean()
        std = spread.std()
        
        if std == 0: return 0.0
        
        return (spread.iloc[-1] - mean) / std

    def analyze(self, data: Dict[str, pd.DataFrame]) -> Optional[Signal]:
        """
        Analyze all pairs and return signals.
        For simplicity, this returns the first valid signal found.
        """
        for asset_a, asset_b in self.symbol_pairs:
            if asset_a not in data or asset_b not in data:
                continue
                
            df_a = data[asset_a]
            df_b = data[asset_b]
            
            if len(df_a) < self.lookback or len(df_b) < self.lookback:
                continue
                
            # Use only close prices for the lookback period
            close_a = df_a['close'].tail(self.lookback)
            close_b = df_b['close'].tail(self.lookback)
            
            z_score = self._calculate_z_score(close_a, close_b)
            
            # Logic:
            # High Z-Score: Asset A is overvalued relative to B -> Sell A, Buy B
            # Low Z-Score: Asset A is undervalued relative to B -> Buy A, Sell B
            
            if z_score > self.z_threshold:
                # Short the Spread: A is high, B is low -> Sell A, Buy B
                logger.info(f"Pairs Signal (Short Spread): {asset_a} high, {asset_b} low. Z={z_score:.2f}")
                return Signal(
                    symbol=f"{asset_a}:{asset_b}",
                    side=OrderSide.SELL, # Signal to "Sell the Spread"
                    strength=min(abs(z_score) / 4.0, 1.0),
                    indicators={"z_score": z_score, "type": "pairs_short"},
                    multi_leg=[
                        {"symbol": asset_a, "side": OrderSide.SELL},
                        {"symbol": asset_b, "side": OrderSide.BUY}
                    ]
                )
            
            elif z_score < -self.z_threshold:
                # Long the Spread: A is low, B is high -> Buy A, Sell B
                logger.info(f"Pairs Signal (Long Spread): {asset_a} low, {asset_b} high. Z={z_score:.2f}")
                return Signal(
                    symbol=f"{asset_a}:{asset_b}",
                    side=OrderSide.BUY, # Signal to "Buy the Spread"
                    strength=min(abs(z_score) / 4.0, 1.0),
                    indicators={"z_score": z_score, "type": "pairs_long"},
                    multi_leg=[
                        {"symbol": asset_a, "side": OrderSide.BUY},
                        {"symbol": asset_b, "side": OrderSide.SELL}
                    ]
                )
                
        return None

    def should_enter(self, signal: Signal, current_price: float, account_balance: float) -> bool:
        """Entry logic for pairs trading."""
        # Simple threshold check
        return signal.strength > 0.3

    def should_exit(self, position: Position, current_price: float, data: pd.DataFrame) -> bool:
        """Exit when Z-Score returns toward the mean."""
        # Note: In a real system, the 'position' symbol would be 'A:B'
        # and we would need to fetch both prices to recalculate Z-score.
        # This is a placeholder for the logic.
        return False
