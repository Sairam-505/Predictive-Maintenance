from abc import ABC, abstractmethod
import numpy as np
import logging
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import joblib

logger = logging.getLogger(__name__)

class BaseModel(ABC):
    """Abstract base class for all predictive models"""
    
    def __init__(self, config: dict, equipment_type: str):
        self.config = config
        self.equipment_type = equipment_type
        self.model = None
        self.is_trained = False
    
    @abstractmethod
    def train(self, X_train, y_train):
        """Train the model"""
        pass
    
    @abstractmethod
    def predict(self, X):
        """Make predictions"""
        pass
    
    def evaluate(self, X_test, y_test):
        """Evaluate model performance"""
        y_pred = self.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_test, y_pred)
        
        metrics = {
            'mse': mse,
            'rmse': rmse,
            'r2': r2
        }
        
        logger.info(f"{self.equipment_type} - {self.__class__.__name__} Evaluation:")
        logger.info(f"  RMSE: {rmse:.4f}")
        logger.info(f"  R²: {r2:.4f}")
        
        return metrics
    
    def save(self, path: str):
        """Save model"""
        joblib.dump(self.model, path)
        logger.info(f"Model saved to {path}")
    
    def load(self, path: str):
        """Load model"""
        self.model = joblib.load(path)
        self.is_trained = True
        logger.info(f"Model loaded from {path}")

class RandomForestModel(BaseModel):
    """Random Forest based RUL prediction"""
    
    def __init__(self, config: dict, equipment_type: str):
        super().__init__(config, equipment_type)
        
        rf_config = config.get("random_forest", {})
        self.model = RandomForestRegressor(
            n_estimators=rf_config.get("n_estimators", 100),
            max_depth=rf_config.get("max_depth", 20),
            min_samples_split=rf_config.get("min_samples_split", 5),
            random_state=42,
            n_jobs=-1
        )
    
    def train(self, X_train, y_train):
        """Train Random Forest"""
        logger.info(f"Training Random Forest for {self.equipment_type}")
        self.model.fit(X_train, y_train)
        self.is_trained = True
        
        # Feature importance
        importances = self.model.feature_importances_
        top_features_idx = np.argsort(importances)[-5:]
        logger.info(f"Top 5 features: {top_features_idx}")
    
    def predict(self, X):
        """Make predictions"""
        if not self.is_trained:
            raise ValueError("Model not trained")
        return self.model.predict(X)

class XGBoostModel(BaseModel):
    """XGBoost based RUL prediction"""
    
    def __init__(self, config: dict, equipment_type: str):
        super().__init__(config, equipment_type)
        import xgboost as xgb
        
        xgb_config = config.get("xgboost", {})
        self.model = xgb.XGBRegressor(
            learning_rate=xgb_config.get("learning_rate", 0.1),
            max_depth=xgb_config.get("max_depth", 7),
            n_estimators=xgb_config.get("n_estimators", 100),
            random_state=42
        )
    
    def train(self, X_train, y_train, X_val=None, y_val=None):
        """Train XGBoost"""
        logger.info(f"Training XGBoost for {self.equipment_type}")
        
        eval_set = [(X_val, y_val)] if X_val is not None else None
        self.model.fit(X_train, y_train, eval_set=eval_set, verbose=False)
        self.is_trained = True
    
    def predict(self, X):
        """Make predictions"""
        if not self.is_trained:
            raise ValueError("Model not trained")
        return self.model.predict(X)

class EnsembleModel(BaseModel):
    """Ensemble combining multiple models"""
    
    def __init__(self, config: dict, equipment_type: str, models: list):
        super().__init__(config, equipment_type)
        self.models = models  # List of trained models
        self.weights = None
    
    def train(self, X_train, y_train):
        """Train individual models"""
        for model in self.models:
            model.train(X_train, y_train)
        self.is_trained = True
    
    def predict(self, X):
        """Average predictions from all models"""
        predictions = np.array([model.predict(X) for model in self.models])
        
        if self.weights is None:
            # Equal weights
            return np.mean(predictions, axis=0)
        else:
            # Weighted average
            return np.average(predictions, axis=0, weights=self.weights)

# Usage:
if __name__ == "__main__":
    import yaml
    
    with open("config/base_config.yaml") as f:
        config = yaml.safe_load(f)
    
    # Train RF model for bearings
    # rf_model = RandomForestModel(config, "bearing")
    # rf_model.train(X_train, y_train)
    # metrics = rf_model.evaluate(X_test, y_test)
