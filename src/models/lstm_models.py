from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

from src.models.base_models import BaseModel

logger = logging.getLogger(__name__)


class LSTMModel(BaseModel):
    """LSTM RUL model for temporal degradation sequences."""

    def __init__(self, config: dict, equipment_type: str):
        super().__init__(config, equipment_type)
        self.sequence_length = config.get("lstm", {}).get("sequence_length", 30)
        self.model = None

    def train(self, X_train, y_train):
        tf = self._tensorflow()
        X_train = self._ensure_3d(X_train)

        lstm_config = self.config.get("lstm", {})
        self.model = tf.keras.Sequential(
            [
                tf.keras.layers.Input(shape=(X_train.shape[1], X_train.shape[2])),
                tf.keras.layers.LSTM(lstm_config.get("units", 64), return_sequences=lstm_config.get("layers", 2) > 1),
                tf.keras.layers.Dropout(lstm_config.get("dropout", 0.2)),
                tf.keras.layers.LSTM(max(16, lstm_config.get("units", 64) // 2)) if lstm_config.get("layers", 2) > 1 else tf.keras.layers.Dense(32, activation="relu"),
                tf.keras.layers.Dense(1),
            ]
        )
        self.model.compile(optimizer="adam", loss="mse", metrics=["mae"])
        self.model.fit(
            X_train,
            np.asarray(y_train),
            epochs=lstm_config.get("epochs", 20),
            batch_size=lstm_config.get("batch_size", 32),
            verbose=0,
        )
        self.is_trained = True
        logger.info("LSTM model trained for %s", self.equipment_type)

    def predict(self, X):
        if not self.is_trained or self.model is None:
            raise ValueError("Model not trained")
        predictions = self.model.predict(self._ensure_3d(X), verbose=0)
        return predictions.ravel()

    def save(self, path: str):
        if self.model is None:
            raise ValueError("Model not trained")
        self.model.save(path)
        logger.info("LSTM model saved to %s", path)

    def load(self, path: str):
        tf = self._tensorflow()
        self.model = tf.keras.models.load_model(Path(path))
        self.is_trained = True
        logger.info("LSTM model loaded from %s", path)

    def _ensure_3d(self, values):
        array = np.asarray(values, dtype=float)
        if array.ndim == 2:
            return array.reshape((array.shape[0], 1, array.shape[1]))
        if array.ndim != 3:
            raise ValueError("LSTM input must be a 2D feature matrix or 3D sequence tensor")
        return array

    def _tensorflow(self):
        try:
            import tensorflow as tf
        except ImportError as exc:
            raise ImportError("tensorflow is required for LSTMModel") from exc
        return tf
