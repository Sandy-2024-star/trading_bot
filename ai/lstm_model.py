"""
LSTM (Long Short-Term Memory) model for price direction prediction.
Uses historical OHLCV data to predict the next candle's directional bias.
"""

import os
import numpy as np
import pandas as pd
from typing import Tuple, Optional
from loguru import logger
from sklearn.preprocessing import MinMaxScaler

# Silence TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout
except ImportError:
    logger.error("TensorFlow not found. Please install it to use LSTM models.")

class LSTMPricePredictor:
    """
    Predicts price direction using an LSTM neural network.
    """

    def __init__(self, symbol: str, lookback: int = 60):
        self.symbol = symbol
        self.lookback = lookback
        self.model: Optional[Sequential] = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.model_path = f"data/models/lstm_{symbol.replace('/', '_')}.h5"
        
        # Ensure model directory exists
        os.makedirs("data/models", exist_ok=True)

    def _prepare_data(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Convert DataFrame to LSTM-ready features and labels.
        Predicts if the next close will be higher (1) or lower (0) than current.
        """
        # We use 'close' price for prediction
        scaled_data = self.scaler.fit_transform(data[['close']].values)
        
        x, y = [], []
        for i in range(self.lookback, len(scaled_data)):
            x.append(scaled_data[i-self.lookback:i, 0])
            # Target: 1 if next price > current price, else 0
            y.append(1 if scaled_data[i, 0] > scaled_data[i-1, 0] else 0)
            
        return np.array(x), np.array(y)

    def build_model(self):
        """Build and compile the LSTM architecture."""
        model = Sequential([
            LSTM(units=50, return_sequences=True, input_shape=(self.lookback, 1)),
            Dropout(0.2),
            LSTM(units=50, return_sequences=False),
            Dropout(0.2),
            Dense(units=25),
            Dense(units=1, activation='sigmoid') # Binary classification
        ])
        
        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        self.model = model
        logger.info(f"Built new LSTM model for {self.symbol}")

    async def train(self, data: pd.DataFrame, epochs: int = 10, batch_size: int = 32):
        """Train the model on historical data."""
        if len(data) < self.lookback + 20:
            logger.warning(f"Not enough data to train LSTM for {self.symbol}")
            return

        x, y = self._prepare_data(data)
        x = np.reshape(x, (x.shape[0], x.shape[1], 1))
        
        if self.model is None:
            self.build_model()
            
        logger.info(f"Training LSTM model for {self.symbol}...")
        self.model.fit(x, y, epochs=epochs, batch_size=batch_size, verbose=0)
        self.model.save(self.model_path)
        logger.info(f"Model saved to {self.model_path}")

    def load(self) -> bool:
        """Load a previously saved model."""
        if os.path.exists(self.model_path):
            try:
                self.model = load_model(self.model_path)
                logger.info(f"Loaded existing LSTM model for {self.symbol}")
                return True
            except Exception as e:
                logger.error(f"Error loading model {self.model_path}: {e}")
        return False

    def predict_direction(self, recent_data: pd.DataFrame) -> float:
        """
        Predict the probability of the next candle being bullish.
        
        Returns:
            Probability (0.0 to 1.0)
        """
        if self.model is None:
            if not self.load():
                return 0.5 # Neutral
                
        if len(recent_data) < self.lookback:
            return 0.5

        # Get latest window
        last_window = recent_data[['close']].tail(self.lookback).values
        scaled_window = self.scaler.transform(last_window)
        x_input = np.reshape(scaled_window, (1, self.lookback, 1))
        
        prediction = self.model.predict(x_input, verbose=0)
        return float(prediction[0][0])
