from __future__ import annotations

import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class InferenceRouter:
    """Route extracted features to equipment-specific prediction models."""

    def __init__(self, equipment_classifier: Any, equipment_models: dict[str, list[Any] | dict[str, Any]]):
        self.equipment_classifier = equipment_classifier
        self.equipment_models = equipment_models

    def infer(self, features: Any) -> dict[str, Any]:
        equipment_type, classifier_confidence = self._classify(features)
        models = self._models_for(equipment_type)

        predictions: list[float] = []
        model_names: list[str] = []
        for name, model in models:
            try:
                prediction = model.predict(features)
                predictions.append(float(np.asarray(prediction).ravel()[0]))
                model_names.append(name)
            except Exception:
                logger.exception("Model %s failed during %s inference", name, equipment_type)

        if not predictions:
            raise RuntimeError(f"No usable models available for equipment type '{equipment_type}'")

        predicted_rul = float(np.average(predictions))
        alert_level = self._alert_level(predicted_rul)

        return {
            "equipment_type": equipment_type,
            "predicted_rul_hours": round(predicted_rul, 2),
            "rul_hours": round(predicted_rul, 2),
            "confidence_score": round(float(classifier_confidence), 2),
            "fault_type": "model_detected_degradation",
            "alert_level": alert_level,
            "health_score": int(np.clip(predicted_rul / 500 * 100, 0, 100)),
            "recommendation": self._recommendation(alert_level, predicted_rul),
            "models_used": model_names,
            "engine": "trained_models",
        }

    def _classify(self, features: Any) -> tuple[str, float]:
        equipment_type, confidence = self.equipment_classifier.predict(features)
        if confidence < 0.5:
            logger.warning("Classifier confidence %.2f is low; falling back to bearing", confidence)
            return "bearing", float(confidence)
        return str(equipment_type), float(confidence)

    def _models_for(self, equipment_type: str) -> list[tuple[str, Any]]:
        selected = self.equipment_models.get(equipment_type) or self.equipment_models.get("bearing")
        if selected is None:
            raise RuntimeError(f"No models configured for '{equipment_type}'")
        if isinstance(selected, dict):
            return list(selected.items())
        return [(model.__class__.__name__, model) for model in selected]

    def _alert_level(self, rul_hours: float) -> str:
        if rul_hours < 24:
            return "critical"
        if rul_hours < 168:
            return "warning"
        return "healthy"

    def _recommendation(self, alert_level: str, rul_hours: float) -> str:
        if alert_level == "critical":
            return f"Immediate maintenance required; model-estimated RUL is {rul_hours:.1f} hours."
        if alert_level == "warning":
            return f"Schedule maintenance within 7 days; model-estimated RUL is {rul_hours:.1f} hours."
        return "Continue normal monitoring and planned maintenance cadence."
