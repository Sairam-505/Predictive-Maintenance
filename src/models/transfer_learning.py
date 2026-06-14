from __future__ import annotations

import copy
import logging
from typing import Any

logger = logging.getLogger(__name__)


class TransferLearningAdapter:
    """Adapt an existing model to a new equipment domain with a small labeled sample."""

    def __init__(self, base_model: Any, feature_adapter: Any | None = None):
        self.base_model = base_model
        self.feature_adapter = feature_adapter
        self.adapted_model = None

    def adapt(self, features: Any, labels: Any):
        self.adapted_model = copy.deepcopy(self.base_model)
        adapted_features = self.transform_features(features)

        if hasattr(self.adapted_model, "train"):
            self.adapted_model.train(adapted_features, labels)
        elif hasattr(self.adapted_model, "fit"):
            self.adapted_model.fit(adapted_features, labels)
        else:
            raise TypeError("Base model must expose train() or fit() for transfer adaptation")

        logger.info("Transfer learning adaptation complete")
        return self.adapted_model

    def predict(self, features: Any):
        if self.adapted_model is None:
            raise ValueError("Call adapt() before predict()")
        adapted_features = self.transform_features(features)
        if hasattr(self.adapted_model, "predict"):
            return self.adapted_model.predict(adapted_features)
        raise TypeError("Adapted model does not expose predict()")

    def transform_features(self, features: Any):
        if self.feature_adapter is None:
            return features
        if hasattr(self.feature_adapter, "transform"):
            return self.feature_adapter.transform(features)
        return self.feature_adapter(features)
