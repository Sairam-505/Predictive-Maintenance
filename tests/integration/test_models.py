import pytest
import numpy as np
import pandas as pd
from src.models.base_models import RandomForestModel, XGBoostModel
from sklearn.model_selection import cross_val_score

def test_random_forest_training():
    """Test Random Forest model training and prediction"""
    config = {
        "random_forest": {
            "n_estimators": 50,
            "max_depth": 10,
            "min_samples_split": 5
        }
    }
    
    # Create synthetic data
    X = np.random.randn(100, 10)
    y = np.random.randint(0, 100, 100)
    
    model = RandomForestModel(config, "bearing")
    model.train(X, y)
    
    # Test prediction
    predictions = model.predict(X[:10])
    assert len(predictions) == 10
    assert all(0 <= p <= 100 for p in predictions)

def test_xgboost_training():
    """Test XGBoost model training and prediction"""
    config = {
        "xgboost": {
            "learning_rate": 0.1,
            "max_depth": 7,
            "n_estimators": 50
        }
    }
    
    X = np.random.randn(100, 10)
    y = np.random.randint(0, 100, 100)
    
    model = XGBoostModel(config, "bearing")
    model.train(X, y)
    
    predictions = model.predict(X[:10])
    assert len(predictions) == 10

def test_cross_validation():
    """Test cross-validation"""
    config = {"random_forest": {"n_estimators": 50}}
    
    X = np.random.randn(100, 10)
    y = np.random.randint(0, 100, 100)
    
    model = RandomForestModel(config, "bearing")
    
    # 5-fold cross validation
    scores = cross_val_score(model.model, X, y, cv=5, scoring='r2')
    
    assert len(scores) == 5
    assert all(-1 <= s <= 1 for s in scores)
