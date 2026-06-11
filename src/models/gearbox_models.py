from src.models.base_models import BaseModel
import numpy as np
import logging
from sklearn.ensemble import RandomForestRegressor

logger = logging.getLogger(__name__)

class GearboxModel(BaseModel):
    """Specialized model for Gearbox Predictive Maintenance"""
    
    def __init__(self, config: dict):
        super().__init__(config, "gearbox")
        self.model = RandomForestRegressor(
            n_estimators=150,
            max_depth=15,
            random_state=42
        )
        
    def train(self, X_train, y_train):
        """Train Gearbox specific model"""
        logger.info(f"Training specialized Gearbox model...")
        self.model.fit(X_train, y_train)
        self.is_trained = True
        logger.info(f"Gearbox model training complete.")

    def predict(self, X):
        """Make predictions for Gearbox"""
        if not self.is_trained:
            raise ValueError("Gearbox model not trained")
        return self.model.predict(X)
