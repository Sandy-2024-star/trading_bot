"""
Correlation Engine for multi-asset risk management.
Calculates relationships between symbols to prevent over-exposure.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from loguru import logger
from datetime import datetime

class CorrelationEngine:
    """
    Calculates and manages market correlations.
    """

    def __init__(self, lookback_days: int = 30):
        self.lookback_days = lookback_days
        self.correlation_matrix: pd.DataFrame = pd.DataFrame()
        self.last_update: Optional[datetime] = None

    def update_matrix(self, price_data: Dict[str, pd.DataFrame]):
        """
        Update the correlation matrix using provided OHLCV data for multiple symbols.
        
        Args:
            price_data: Dict mapping symbol -> DataFrame with 'close' prices
        """
        try:
            if not price_data:
                return

            # Extract close prices into a single DataFrame
            close_prices = {}
            for symbol, df in price_data.items():
                if not df.empty and 'close' in df.columns:
                    # Use timestamp as index for alignment
                    temp_df = df.set_index('timestamp')['close']
                    # Handle duplicate timestamps by taking the last
                    temp_df = temp_df[~temp_df.index.duplicated(keep='last')]
                    close_prices[symbol] = temp_df

            if not close_prices:
                return

            combined_df = pd.DataFrame(close_prices)
            
            # Calculate percentage returns for stationary data
            returns_df = combined_df.pct_change().dropna()
            
            # Calculate Pearson correlation
            self.correlation_matrix = returns_df.corr(method='pearson')
            self.last_update = datetime.now()
            
            logger.info(f"Correlation matrix updated for symbols: {list(close_prices.keys())}")
            
        except Exception as e:
            logger.error(f"Error updating correlation matrix: {e}")

    def get_correlation(self, symbol1: str, symbol2: str) -> float:
        """Get correlation coefficient between two symbols."""
        if self.correlation_matrix.empty:
            return 0.0
            
        try:
            if symbol1 in self.correlation_matrix.index and symbol2 in self.correlation_matrix.columns:
                return float(self.correlation_matrix.loc[symbol1, symbol2])
        except Exception:
            pass
        return 0.0

    def check_trade_correlation(
        self, 
        new_symbol: str, 
        open_positions: List[str], 
        threshold: float = 0.8
    ) -> List[str]:
        """
        Check if a new symbol is too highly correlated with existing open positions.
        
        Returns:
            List of symbols that violate the correlation threshold.
        """
        violations = []
        for open_symbol in open_positions:
            corr = self.get_correlation(new_symbol, open_symbol)
            if abs(corr) >= threshold:
                logger.warning(f"High correlation detected: {new_symbol} vs {open_symbol} ({corr:.2f})")
                violations.append(open_symbol)
        
        return violations

    def get_matrix_dict(self) -> Dict:
        """Return the matrix as a serializable dictionary for the dashboard."""
        if self.correlation_matrix.empty:
            return {}
            
        return {
            "symbols": self.correlation_matrix.columns.tolist(),
            "values": self.correlation_matrix.values.tolist(),
            "updated_at": self.last_update.isoformat() if self.last_update else None
        }
