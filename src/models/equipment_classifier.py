from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import logging
import numpy as np

logger = logging.getLogger(__name__)

class EquipmentClassifier:
    """
    Classify incoming data to equipment type.
    
    This router directs data to the appropriate specialized model.
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.equipment_types = config.get("equipment_types", [])
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_trained = False
    
    def train(self, features, labels):
        """
        Train equipment classifier
        
        Args:
            features: DataFrame with feature columns
            labels: Series with equipment type labels
        """
        # Scale features
        features_scaled = self.scaler.fit_transform(features)
        
        # Train classifier
        self.model.fit(features_scaled, labels)
        self.is_trained = True
        
        logger.info(f"Equipment classifier trained. Classes: {self.model.classes_}")
    
    def predict(self, features):
        """
        Predict equipment type
        
        Args:
            features: DataFrame with feature columns
        
        Returns:
            equipment_type: Predicted equipment type
            confidence: Prediction confidence (0-1)
        """
        if not self.is_trained:
            raise ValueError("Model not trained yet")
        
        features_scaled = self.scaler.transform(features)
        
        equipment_type = self.model.predict(features_scaled)[0]
        confidence = np.max(self.model.predict_proba(features_scaled))
        
        return equipment_type, confidence
    
    def save(self, path: str):
        """Save classifier"""
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler
        }, path)
        logger.info(f"Equipment classifier saved to {path}")
    
    def load(self, path: str):
        """Load classifier"""
        data = joblib.load(path)
        self.model = data['model']
        self.scaler = data['scaler']
        self.is_trained = True
        logger.info(f"Equipment classifier loaded from {path}")
