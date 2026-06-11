from pathlib import Path
import json
import logging
from typing import Dict, Tuple
import numpy as np
from sklearn.model_selection import train_test_split
from src.models.base_models import RandomForestModel, XGBoostModel, EnsembleModel

logger = logging.getLogger(__name__)

class ModelTrainer:
    """Train and validate models for each equipment type"""
    
    def __init__(self, config: dict, output_dir: str = "./models/final"):
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.trained_models = {}
        self.results = {}
    
    def train_equipment_models(self, equipment_type: str, features, labels, 
                               test_size: float = 0.2, val_size: float = 0.1):
        """
        Train multiple models for a specific equipment type
        
        Args:
            equipment_type: "bearing", "motor", "pump", etc.
            features: Feature DataFrame
            labels: Target variable (RUL)
            test_size: Fraction for test set
            val_size: Fraction for validation set from remaining data
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Training models for {equipment_type}")
        logger.info(f"{'='*60}")
        
        # Split data: train / (val + test)
        X_train, X_temp, y_train, y_temp = train_test_split(
            features, labels, test_size=(test_size + val_size), random_state=42
        )
        
        # Split temp into val and test
        val_test_size = val_size / (val_size + test_size)
        X_val, X_test, y_val, y_test = train_test_split(
            X_temp, y_temp, test_size=val_test_size, random_state=42
        )
        
        logger.info(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
        
        # Initialize models
        models_to_train = {
            'random_forest': RandomForestModel(self.config, equipment_type),
            'xgboost': XGBoostModel(self.config, equipment_type),
        }
        
        # Train each model
        equipment_results = {}
        for model_name, model in models_to_train.items():
            logger.info(f"\nTraining {model_name}...")
            model.train(X_train, y_train)
            
            # Evaluate
            metrics = model.evaluate(X_test, y_test)
            equipment_results[model_name] = metrics
            
            # Save model
            model_path = self.output_dir / f"{equipment_type}_{model_name}.pkl"
            model.save(str(model_path))
            logger.info(f"Saved to {model_path}")
        
        # Train ensemble
        logger.info(f"\nTraining ensemble...")
        ensemble = EnsembleModel(
            self.config, 
            equipment_type,
            list(models_to_train.values())
        )
        ensemble_metrics = ensemble.evaluate(X_test, y_test)
        equipment_results['ensemble'] = ensemble_metrics
        
        self.trained_models[equipment_type] = models_to_train
        self.results[equipment_type] = equipment_results
        
        return equipment_results
    
    def save_results(self, filename: str = "training_results.json"):
        """Save training results to JSON"""
        results_path = self.output_dir / filename
        
        # Convert to JSON-serializable format
        results_json = {}
        for equipment, metrics_dict in self.results.items():
            results_json[equipment] = {}
            for model, metrics in metrics_dict.items():
                results_json[equipment][model] = {
                    k: float(v) for k, v in metrics.items()
                }
        
        with open(results_path, 'w') as f:
            json.dump(results_json, f, indent=2)
        
        logger.info(f"Results saved to {results_path}")
    
    def generate_report(self):
        """Generate training report"""
        report = "="*60 + "\n"
        report += "TRAINING RESULTS SUMMARY\n"
        report += "="*60 + "\n\n"
        
        for equipment, metrics_dict in self.results.items():
            report += f"\n{equipment.upper()}\n"
            report += "-"*40 + "\n"
            
            for model, metrics in metrics_dict.items():
                report += f"  {model}:\n"
                for metric, value in metrics.items():
                    report += f"    {metric}: {value:.4f}\n"
        
        return report

# Usage:
if __name__ == "__main__":
    import yaml
    import pandas as pd
    
    with open("config/base_config.yaml") as f:
        config = yaml.safe_load(f)
    
    trainer = ModelTrainer(config)
    
    # Load processed bearing data
    # bearing_features = pd.read_csv("data/processed/bearing_features.csv")
    # bearing_labels = pd.read_csv("data/processed/bearing_labels.csv")
    
    # Train
    # results = trainer.train_equipment_models(
    #     "bearing",
    #     bearing_features,
    #     bearing_labels.values.ravel()
    # )
    
    # Save
    # trainer.save_results()
    # print(trainer.generate_report())
