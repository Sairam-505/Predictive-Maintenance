"""
Convert different dataset formats to unified schema
"""
import pandas as pd
import numpy as np
from datetime import datetime

class UnifiedDataSchema:
    """
    All datasets mapped to common format:
    {
        'timestamp': datetime,
        'equipment_id': str,
        'equipment_type': str,
        'sensors': {
            'sensor_name': {'data': array, 'sampling_rate': float, 'unit': str},
            ...
        },
        'fault_type': str,
        'severity': int,  # 0=healthy, 1=minor, 2=moderate, 3=severe
        'rul_hours': int,
        'operating_conditions': {
            'speed': float,
            'load': float,
            'temperature': float
        }
    }
    """
    
    @staticmethod
    def from_cwru(raw_data: pd.DataFrame, equipment_id: str) -> dict:
        """Convert CWRU format to unified schema"""
        # CWRU stores .mat files with structure:
        # X###_DE_time, X###_FE_time, X###_BA_time (vibration)
        # Simplified mapping logic for demonstration
        return {
            'timestamp': datetime.now(),
            'equipment_id': equipment_id,
            'equipment_type': 'bearing',
            'sensors': {
                'vibration_DE': {'data': raw_data.iloc[:, 0].values if not raw_data.empty else np.array([]), 'sampling_rate': 12000.0, 'unit': 'g'},
            },
            'fault_type': 'inner_race',
            'severity': 2,
            'rul_hours': 100,
            'operating_conditions': {
                'speed': 1797.0,
                'load': 0.0,
                'temperature': 25.0
            }
        }
    
    @staticmethod
    def from_paderborn(raw_data: pd.DataFrame, equipment_id: str) -> dict:
        """Convert Paderborn format to unified schema"""
        return {
            'timestamp': datetime.now(),
            'equipment_id': equipment_id,
            'equipment_type': 'motor',
            'sensors': {
                'current_phase_1': {'data': np.array([]), 'sampling_rate': 64000.0, 'unit': 'A'},
                'vibration': {'data': np.array([]), 'sampling_rate': 64000.0, 'unit': 'm/s^2'}
            },
            'fault_type': 'healthy',
            'severity': 0,
            'rul_hours': 500,
            'operating_conditions': {
                'speed': 1500.0,
                'load': 0.7,
                'torque': 0.1
            }
        }
    
    @staticmethod
    def from_cmapss(raw_data: pd.DataFrame, equipment_id: str) -> dict:
        """Convert CMAPSS format to unified schema"""
        return {
            'timestamp': datetime.now(),
            'equipment_id': equipment_id,
            'equipment_type': 'turbine',
            'sensors': {f'sensor_{i}': {'data': np.array([]), 'sampling_rate': 1.0, 'unit': 'various'} for i in range(1, 22)},
            'fault_type': 'degradation',
            'severity': 1,
            'rul_hours': 125,
            'operating_conditions': {
                'altitude': 10000.0,
                'mach': 0.8,
                'throttle': 100.0
            }
        }
    
    @staticmethod
    def from_hydraulic(raw_data: pd.DataFrame, equipment_id: str) -> dict:
        """Convert hydraulic dataset to unified schema"""
        return {
            'timestamp': datetime.now(),
            'equipment_id': equipment_id,
            'equipment_type': 'pump',
            'sensors': {
                'pressure': {'data': np.array([]), 'sampling_rate': 100.0, 'unit': 'bar'},
                'flow': {'data': np.array([]), 'sampling_rate': 10.0, 'unit': 'L/min'}
            },
            'fault_type': 'valve_degradation',
            'severity': 1,
            'rul_hours': 200,
            'operating_conditions': {
                'cooler_power': 100.0,
                'valve_setting': 100.0
            }
        }
