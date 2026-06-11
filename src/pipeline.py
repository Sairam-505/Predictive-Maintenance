from sklearn.pipeline import Pipeline as SKLPipeline
from src.preprocessing.cleaner import DataCleaner, DataNormalizer
from src.features.extractor import FeatureExtractor
import logging

logger = logging.getLogger(__name__)

class ProcessingPipeline:
    """End-to-end data processing pipeline"""
    
    def __init__(self, config: dict):
        self.config = config
        self.cleaner = DataCleaner(config["preprocessing"])
        self.normalizer = DataNormalizer(config["preprocessing"]["normalization_method"])
        self.feature_extractor = FeatureExtractor(config["feature_engineering"])
    
    def fit(self, raw_data):
        """Learn normalization parameters from training data"""
        logger.info("Fitting pipeline...")
        
        # Clean
        data_clean = self.cleaner.clean(raw_data)
        
        # Fit normalizer (must happen before feature extraction)
        self.normalizer.fit(data_clean)
        
        logger.info("Pipeline fitted successfully")
    
    def transform(self, raw_data):
        """Apply all transformations"""
        # Clean
        data_clean = self.cleaner.clean(raw_data)
        
        # Normalize
        data_norm = self.normalizer.transform(data_clean)
        
        # Extract features
        features = self.feature_extractor.extract(data_norm)
        
        return features
    
    def fit_transform(self, raw_data):
        """Fit and transform"""
        self.fit(raw_data)
        return self.transform(raw_data)

# Usage:
if __name__ == "__main__":
    import yaml
    
    with open("config/base_config.yaml") as f:
        config = yaml.safe_load(f)
    
    pipeline = ProcessingPipeline(config)
    
    # This will be used in training and inference
    # processed_data = pipeline.fit_transform(raw_data)
