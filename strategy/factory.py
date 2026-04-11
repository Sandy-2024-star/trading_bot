"""
Strategy Factory for creating configured strategy instances.
Loads symbol-specific parameters from configuration files.
"""

import os
import json
from typing import Optional, Dict
from loguru import logger

from strategy.signal_strategy import TechnicalSignalStrategy
from strategy.mean_reversion import MeanReversionStrategy
from strategy.pairs_trading import PairsTradingStrategy
from config.config import config

def load_symbol_params() -> Dict[str, Dict]:
    """
    Load symbol-specific indicator parameters from the JSON config file.
    """
    config_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_dir = os.path.join(config_dir, "config")
    params_file = os.path.join(config_dir, "symbol_params.json")
    
    if os.path.exists(params_file):
        try:
            with open(params_file, 'r') as f:
                params = json.load(f)
                logger.info(f"Loaded tuned parameters for symbols: {list(params.keys())}")
                return params
        except Exception as e:
            logger.error(f"Error loading tuned parameters from {params_file}: {e}")
            
    return {}

def create_strategy(name: str = "DefaultStrategy", strategy_type: str = "technical") -> TechnicalSignalStrategy:
    """
    Create and configure a strategy instance.
    """
    symbol_params = load_symbol_params()
    
    if strategy_type == "technical":
        logger.info(f"Creating TechnicalSignalStrategy: {name}")
        return TechnicalSignalStrategy(
            name=name,
            symbol_params=symbol_params,
            signal_threshold=0.4 # More aggressive default for multi-indicator
        )
    
    if strategy_type == "mean_reversion":
        logger.info(f"Creating MeanReversionStrategy: {name}")
        return MeanReversionStrategy(
            name=name,
            symbol_params=symbol_params,
            z_threshold=2.0
        )

    if strategy_type == "pairs":
        logger.info(f"Creating PairsTradingStrategy: {name}")
        return PairsTradingStrategy(
            name=name,
            z_score_entry=2.0
        )
    
    # Fallback to default
    logger.warning(f"Unknown strategy type '{strategy_type}', falling back to TechnicalSignalStrategy")
    return TechnicalSignalStrategy(name=name, symbol_params=symbol_params)
