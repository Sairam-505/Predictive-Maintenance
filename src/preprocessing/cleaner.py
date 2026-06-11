import numpy as np
import pandas as pd
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class DataCleaner:
    """Clean and prepare raw sensor data"""
    
    def __init__(self, config: dict):
        self.config = config
    
    def clean(self, data: pd.DataFrame) -> pd.DataFrame:
        """Apply all cleaning steps"""
        data = data.copy()
        
        # Step 1: Remove duplicates
        initial_rows = len(data)
        data = data.drop_duplicates()
        logger.info(f"Removed {initial_rows - len(data)} duplicate rows")
        
        # Step 2: Handle missing values
        data = self._handle_missing_values(data)
        
        # Step 3: Remove outliers
        data = self._remove_outliers(data)
        
        # Step 4: Validate data
        self._validate_data(data)
        
        return data
    
    def _handle_missing_values(self, data: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values based on config"""
        method = self.config.get("handle_missing", "forward_fill")
        
        if method == "drop":
            data = data.dropna()
        elif method == "forward_fill":
            data = data.fillna(method='ffill').fillna(method='bfill')
        elif method == "interpolate":
            data = data.interpolate(method='linear')
        
        logger.info(f"Handled missing values using {method}")
        return data
    
    def _remove_outliers(self, data: pd.DataFrame) -> pd.DataFrame:
        """Remove statistical outliers"""
        method = self.config.get("outlier_method", "iqr")
        threshold = self.config.get("outlier_threshold", 3)
        
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        
        if method == "iqr":
            for col in numeric_cols:
                Q1 = data[col].quantile(0.25)
                Q3 = data[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - threshold * IQR
                upper_bound = Q3 + threshold * IQR
                
                before = len(data)
                data = data[(data[col] >= lower_bound) & (data[col] <= upper_bound)]
                logger.info(f"Removed {before - len(data)} outliers from {col}")
        
        elif method == "zscore":
            for col in numeric_cols:
                z_scores = np.abs((data[col] - data[col].mean()) / data[col].std())
                before = len(data)
                data = data[z_scores < threshold]
                logger.info(f"Removed {before - len(data)} outliers from {col}")
        
        return data
    
    def _validate_data(self, data: pd.DataFrame) -> None:
        """Validate data quality"""
        if len(data) == 0:
            raise ValueError("Data is empty after cleaning")
        
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            raise ValueError("No numeric columns found in data")
        
        logger.info(f"Data validation passed: {len(data)} rows, {len(numeric_cols)} numeric columns")

class DataNormalizer:
    """Normalize features to similar scales"""
    
    def __init__(self, method: str = "minmax"):
        self.method = method
        self.scale_params = {}
    
    def fit(self, data: pd.DataFrame) -> None:
        """Learn normalization parameters"""
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            if self.method == "minmax":
                self.scale_params[col] = {
                    "min": data[col].min(),
                    "max": data[col].max()
                }
            elif self.method == "zscore":
                self.scale_params[col] = {
                    "mean": data[col].mean(),
                    "std": data[col].std()
                }
    
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """Apply normalization"""
        data = data.copy()
        
        for col in self.scale_params.keys():
            if self.method == "minmax":
                min_val = self.scale_params[col]["min"]
                max_val = self.scale_params[col]["max"]
                data[col] = (data[col] - min_val) / (max_val - min_val + 1e-8)
            
            elif self.method == "zscore":
                mean = self.scale_params[col]["mean"]
                std = self.scale_params[col]["std"]
                data[col] = (data[col] - mean) / (std + 1e-8)
        
        return data
    
    def fit_transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """Fit and transform in one step"""
        self.fit(data)
        return self.transform(data)

# Usage example:
if __name__ == "__main__":
    config = {
        "handle_missing": "forward_fill",
        "outlier_method": "iqr",
        "outlier_threshold": 3
    }
    
    cleaner = DataCleaner(config)
    normalizer = DataNormalizer("minmax")
    
    # Load data
    data = pd.read_csv("data.csv")
    
    # Clean
    data_clean = cleaner.clean(data)
    
    # Normalize
    data_norm = normalizer.fit_transform(data_clean)
