import numpy as np
import pandas as pd
from scipy import signal, fft
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class FeatureExtractor:
    """Extract domain-agnostic and equipment-specific features"""
    
    def __init__(self, config: dict):
        self.config = config
        self.time_domain_features = config.get("time_domain", [])
        self.freq_domain_features = config.get("frequency_domain", [])
        self.time_freq_features = config.get("time_frequency", [])
    
    def extract(self, data: pd.DataFrame, window_size: int = 2560) -> pd.DataFrame:
        """
        Extract features from signal data
        
        Args:
            data: DataFrame with signal columns
            window_size: Samples per window for feature extraction
        
        Returns:
            DataFrame with extracted features
        """
        features_list = []
        
        # Get numeric columns (sensor signals)
        signal_cols = data.select_dtypes(include=[np.number]).columns
        
        # Process each window
        for i in range(0, len(data) - window_size, window_size):
            window_data = data.iloc[i:i+window_size][signal_cols]
            window_features = {}
            
            # Add timestamp
            window_features['timestamp'] = data.index[i]
            
            # Extract features for each signal
            for col in signal_cols:
                signal_vals = window_data[col].values
                
                # Time domain
                if "mean" in self.time_domain_features:
                    window_features[f'{col}_mean'] = np.mean(signal_vals)
                
                if "std" in self.time_domain_features:
                    window_features[f'{col}_std'] = np.std(signal_vals)
                
                if "rms" in self.time_domain_features:
                    window_features[f'{col}_rms'] = np.sqrt(np.mean(signal_vals**2))
                
                if "kurtosis" in self.time_domain_features:
                    from scipy.stats import kurtosis
                    window_features[f'{col}_kurtosis'] = kurtosis(signal_vals)
                
                if "skewness" in self.time_domain_features:
                    from scipy.stats import skew
                    window_features[f'{col}_skewness'] = skew(signal_vals)
                
                if "crest_factor" in self.time_domain_features:
                    window_features[f'{col}_crest_factor'] = np.max(np.abs(signal_vals)) / np.sqrt(np.mean(signal_vals**2))
                
                # Frequency domain (FFT)
                if "fft" in self.freq_domain_features:
                    fft_vals = np.abs(fft.fft(signal_vals))
                    window_features[f'{col}_fft_mean'] = np.mean(fft_vals)
                    window_features[f'{col}_fft_std'] = np.std(fft_vals)
                    window_features[f'{col}_fft_max'] = np.max(fft_vals)
                
                if "spectral_centroid" in self.freq_domain_features:
                    frequencies = np.fft.fftfreq(len(signal_vals))
                    fft_vals = np.abs(fft.fft(signal_vals))
                    centroid = np.sum(frequencies * fft_vals) / np.sum(fft_vals)
                    window_features[f'{col}_spectral_centroid'] = centroid
            
            features_list.append(window_features)
        
        features_df = pd.DataFrame(features_list)
        logger.info(f"Extracted {len(features_df)} feature windows with {len(features_df.columns)} features")
        
        return features_df

class EquipmentSpecificFeatures:
    """Extract equipment-specific features"""
    
    @staticmethod
    def bearing_features(signal: np.ndarray, sampling_rate: int = 25600) -> Dict:
        """
        Extract bearing-specific features
        
        Bearing fault frequencies based on geometry:
        - Ball Pass Frequency Outer race (BPFO)
        - Ball Pass Frequency Inner race (BPFI)
        - Ball Spin Frequency (BSF)
        - Fundamental Train Frequency (FTF)
        """
        # Bearing parameters (example: 6203 bearing)
        pitch_diameter = 34.55  # mm
        ball_diameter = 7.92    # mm
        contact_angle = 0       # degrees
        num_balls = 8
        
        # Shaft speed (RPM) - need to estimate from data or provide
        shaft_speed = 1500  # RPM - would be detected in real data
        shaft_freq = shaft_speed / 60  # Hz
        
        # Calculate bearing fault frequencies
        bpfo = (num_balls / 2) * shaft_freq * (1 - (ball_diameter / pitch_diameter) * np.cos(contact_angle))
        bpfi = (num_balls / 2) * shaft_freq * (1 + (ball_diameter / pitch_diameter) * np.cos(contact_angle))
        bsf = (shaft_freq / 2) * (1 - (ball_diameter / pitch_diameter) * np.cos(contact_angle))
        ftf = (1 / 2) * (1 - (ball_diameter / pitch_diameter) * np.cos(contact_angle))
        
        features = {
            'bearing_bpfo': bpfo,
            'bearing_bpfi': bpfi,
            'bearing_bsf': bsf,
            'bearing_ftf': ftf,
        }
        
        # Extract energy around fault frequencies
        fft_vals = np.abs(fft.fft(signal))
        freqs = np.fft.fftfreq(len(signal), 1/sampling_rate)
        
        bandwidth = 10  # Hz around each fault frequency
        for fault_name, fault_freq in [("bpfo", bpfo), ("bpfi", bpfi), ("bsf", bsf)]:
            freq_range = (freqs >= fault_freq - bandwidth) & (freqs <= fault_freq + bandwidth)
            features[f'bearing_{fault_name}_energy'] = np.sum(fft_vals[freq_range]**2)
        
        return features
    
    @staticmethod
    def motor_features(signal: np.ndarray) -> Dict:
        """Extract motor-specific features (slip, synchronous speed, etc.)"""
        # Motor slip = (synchronous_speed - actual_speed) / synchronous_speed
        # Detected from current signature analysis (MCSA)
        features = {
            'motor_frequency_component': np.max(np.abs(fft.fft(signal))),
            'motor_vibration_amplitude': np.max(np.abs(signal)),
        }
        return features
    
    @staticmethod
    def pump_features(signal: np.ndarray) -> Dict:
        """Extract pump-specific features (flow rate, pressure pulsations, etc.)"""
        features = {
            'pump_flow_ripple': np.std(signal),
            'pump_pressure_amplitude': np.max(np.abs(signal)),
            'pump_discharge_periodicity': np.abs(fft.fft(signal))[1],  # 1st harmonic
        }
        return features

# Usage:
if __name__ == "__main__":
    import yaml
    
    with open("config/base_config.yaml") as f:
        config = yaml.safe_load(f)
    
    extractor = FeatureExtractor(config["feature_engineering"])
    
    # Load data
    # data = pd.read_csv("processed_data.csv")
    
    # Extract features
    # features = extractor.extract(data)
    # print(f"Features shape: {features.shape}")
