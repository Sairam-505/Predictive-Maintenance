from __future__ import annotations

import logging
from typing import Any

import numpy as np
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Isolation Forest wrapper for unexpected sensor fault detection."""

    def __init__(self, config: dict | None = None):
        config = config or {}
        iso_config = config.get("isolation_forest", config)
        self.model = IsolationForest(
            contamination=iso_config.get("contamination", 0.1),
            n_estimators=iso_config.get("n_estimators", 100),
            random_state=42,
        )
        self.is_trained = False

    def train(self, features: Any):
        self.model.fit(features)
        self.is_trained = True
        logger.info("Anomaly detector trained")

    def predict(self, features: Any) -> np.ndarray:
        if not self.is_trained:
            raise ValueError("Anomaly detector not trained")
        return self.model.predict(features)

    def score(self, features: Any) -> np.ndarray:
        if not self.is_trained:
            raise ValueError("Anomaly detector not trained")
        return -self.model.score_samples(features)


class HybridFaultDetection:
    """Combine RUL model output with anomaly scores for operational alerting."""

    def __init__(self, rul_model: Any, anomaly_detector: AnomalyDetector, anomaly_threshold: float = 0.6):
        self.rul_model = rul_model
        self.anomaly_detector = anomaly_detector
        self.anomaly_threshold = anomaly_threshold

    def predict(self, features: Any) -> dict[str, Any]:
        rul_predictions = np.asarray(self.rul_model.predict(features), dtype=float)
        anomaly_scores = self.anomaly_detector.score(features)
        fault_flags = anomaly_scores >= self.anomaly_threshold

        return {
            "rul_predictions": rul_predictions.tolist(),
            "anomaly_scores": anomaly_scores.tolist(),
            "fault_flags": fault_flags.tolist(),
            "fault_type": "unexpected_anomaly" if bool(np.any(fault_flags)) else "model_detected_degradation",
        }
