from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd


EPSILON = 1e-8


@dataclass(frozen=True)
class SensorStats:
    rms: float
    kurtosis: float
    peak_amplitude: float
    std: float
    crest_factor: float
    pressure_std: float
    flow_loss: float
    spectral_energy: float
    anomaly_z_score: float
    temperature_drift: float
    turbine_deviation: float


class PhysicsSimulationEngine:
    """Physics-inspired predictive maintenance engine used before trained models exist."""

    BASE_RUL = {
        "bearing": 500.0,
        "motor": 2000.0,
        "pump": 720.0,
        "gearbox": 400.0,
        "turbine": 350.0,
        "default": 300.0,
    }

    RMS_LIMITS = {
        "bearing": 10.0,
        "motor": 8.0,
        "pump": 12.0,
        "gearbox": 15.0,
        "default": 10.0,
    }

    def analyze(self, data: pd.DataFrame, equipment_id: str | None = None) -> dict[str, Any]:
        numeric_data = self._numeric_frame(data)
        equipment_type = self.detect_equipment_type(data)
        stats = self.compute_statistics(numeric_data)
        rul_hours = self.calculate_rul(equipment_type, stats)
        fault_type = self.detect_fault_type(data, stats)
        alert_level = self.alert_level(rul_hours)
        confidence_score = self.confidence_score(stats)

        return {
            "equipment_id": equipment_id or "uploaded-csv",
            "equipment_type": equipment_type,
            "predicted_rul_hours": round(rul_hours, 2),
            "rul_hours": round(rul_hours, 2),
            "confidence_score": confidence_score,
            "fault_type": fault_type,
            "alert_level": alert_level,
            "health_score": self.health_score(equipment_type, rul_hours),
            "recommendation": self.maintenance_recommendation(alert_level, fault_type, rul_hours),
            "sensor_statistics": {
                "rms": round(stats.rms, 4),
                "kurtosis": round(stats.kurtosis, 4),
                "peak_amplitude": round(stats.peak_amplitude, 4),
                "standard_deviation": round(stats.std, 4),
                "crest_factor": round(stats.crest_factor, 4),
                "temperature_drift": round(stats.temperature_drift, 4),
            },
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "engine": "simulation",
        }

    def detect_equipment_type(self, data: pd.DataFrame) -> str:
        columns = " ".join(str(col).lower() for col in data.columns)

        if any(token in columns for token in ("vibration", "vib", "accel", "accelerometer")):
            return "bearing"
        if any(token in columns for token in ("current", "stator", "voltage", "motor")):
            return "motor"
        if any(token in columns for token in ("pressure", "flow", "pump")):
            return "pump"
        if any(token in columns for token in ("gear", "torque", "gearbox")):
            return "gearbox"
        if "cycle" in columns or any(str(col).lower().startswith("sensor_") for col in data.columns):
            return "turbine"
        return "default"

    def compute_statistics(self, numeric_data: pd.DataFrame) -> SensorStats:
        values = numeric_data.to_numpy(dtype=float).ravel()
        values = values[np.isfinite(values)]
        if values.size == 0:
            values = np.array([0.0])

        rms = float(np.sqrt(np.mean(np.square(values))))
        peak = float(np.max(np.abs(values)))
        std = float(np.std(values))
        crest = float(peak / (rms + EPSILON))
        kurt = self._kurtosis(values)

        pressure_cols = [col for col in numeric_data.columns if "pressure" in str(col).lower()]
        flow_cols = [col for col in numeric_data.columns if "flow" in str(col).lower()]
        temperature_cols = [col for col in numeric_data.columns if "temp" in str(col).lower()]
        sensor_cols = [col for col in numeric_data.columns if str(col).lower().startswith("sensor_")]

        pressure_std = self._finite(float(numeric_data[pressure_cols].std().mean()), std) if pressure_cols else std
        flow_loss = self._finite(self._flow_loss(numeric_data[flow_cols]), 0.0) if flow_cols else min(0.85, max(0.0, std / 20.0))
        spectral_energy = self._spectral_energy(values)
        anomaly_z = float(np.max(np.abs((values - np.mean(values)) / (np.std(values) + EPSILON))))
        temperature_drift = self._finite(self._temperature_drift(numeric_data[temperature_cols]), 0.0) if temperature_cols else 0.0
        turbine_deviation = self._finite(self._turbine_deviation(numeric_data[sensor_cols]), 0.0) if sensor_cols else 0.0

        return SensorStats(
            rms=rms,
            kurtosis=kurt,
            peak_amplitude=peak,
            std=std,
            crest_factor=crest,
            pressure_std=pressure_std,
            flow_loss=flow_loss,
            spectral_energy=spectral_energy,
            anomaly_z_score=anomaly_z,
            temperature_drift=temperature_drift,
            turbine_deviation=turbine_deviation,
        )

    def calculate_rul(self, equipment_type: str, stats: SensorStats) -> float:
        equipment = equipment_type if equipment_type in self.BASE_RUL else "default"
        base = self.BASE_RUL[equipment]

        if equipment == "bearing":
            rms_factor = 1 - stats.rms / self.RMS_LIMITS["bearing"]
            kurtosis_factor = max(0.1, 1 - (stats.kurtosis - 3) / 5)
            rul = base * rms_factor * kurtosis_factor
        elif equipment == "motor":
            rms_factor = 1 - stats.rms / self.RMS_LIMITS["motor"]
            kurtosis_factor = max(0.2, 1 - max(0.0, stats.kurtosis - 3) / 6)
            rul = base * rms_factor * kurtosis_factor
        elif equipment == "pump":
            nominal_pressure = max(stats.peak_amplitude, stats.pressure_std, 1.0)
            rul = base * (1 - stats.pressure_std / nominal_pressure) * (1 - stats.flow_loss)
        elif equipment == "gearbox":
            baseline_energy = max(stats.spectral_energy * 1.35, 1.0)
            rul = base * (baseline_energy / (stats.spectral_energy + EPSILON))
        elif equipment == "turbine":
            rul = base * (1 - stats.turbine_deviation)
        else:
            rul = base * max(0.0, 1 - stats.anomaly_z_score / 5.0)

        return float(np.clip(rul, 1.0, base))

    def detect_fault_type(self, data: pd.DataFrame, stats: SensorStats) -> str:
        if stats.temperature_drift > 12:
            return "overheating"
        if stats.kurtosis > 8:
            return "inner_race_fault"
        if 5 <= stats.kurtosis <= 8:
            return "outer_race_fault"
        if stats.rms > 0.7 * self.RMS_LIMITS.get(self.detect_equipment_type(data), 10.0):
            return "rolling_element_wear"
        return "normal_degradation"

    def alert_level(self, rul_hours: float) -> str:
        if rul_hours < 24:
            return "critical"
        if rul_hours < 168:
            return "warning"
        return "healthy"

    def confidence_score(self, stats: SensorStats) -> float:
        severity = min(1.0, (stats.rms / 15.0 + max(0.0, stats.kurtosis - 3) / 10.0) / 2.0)
        return round(float(np.clip(0.78 + severity * 0.17, 0.78, 0.95)), 2)

    def health_score(self, equipment_type: str, rul_hours: float) -> int:
        base = self.BASE_RUL.get(equipment_type, self.BASE_RUL["default"])
        return int(np.clip((self._finite(rul_hours, 1.0) / base) * 100, 0, 100))

    def maintenance_recommendation(self, alert_level: str, fault_type: str, rul_hours: float) -> str:
        if alert_level == "critical":
            return f"Schedule immediate inspection for {fault_type}; estimated RUL is {rul_hours:.1f} hours."
        if alert_level == "warning":
            return f"Plan maintenance within 7 days and monitor {fault_type} indicators closely."
        return "Continue normal monitoring; no immediate maintenance action is required."

    def _numeric_frame(self, data: pd.DataFrame) -> pd.DataFrame:
        numeric_data = data.select_dtypes(include=[np.number]).copy()
        if numeric_data.empty:
            raise ValueError("CSV must contain at least one numeric sensor column")
        return numeric_data.replace([np.inf, -np.inf], np.nan).ffill().bfill().fillna(0.0)

    def _flow_loss(self, flow_data: pd.DataFrame) -> float:
        if flow_data.empty:
            return 0.0
        first = float(flow_data.head(max(1, len(flow_data) // 10)).mean().mean())
        last = float(flow_data.tail(max(1, len(flow_data) // 10)).mean().mean())
        return float(np.clip((first - last) / (abs(first) + EPSILON), 0.0, 0.9))

    def _temperature_drift(self, temperature_data: pd.DataFrame) -> float:
        if temperature_data.empty:
            return 0.0
        first = float(temperature_data.head(max(1, len(temperature_data) // 10)).mean().mean())
        last = float(temperature_data.tail(max(1, len(temperature_data) // 10)).mean().mean())
        return last - first

    def _turbine_deviation(self, sensor_data: pd.DataFrame) -> float:
        if sensor_data.empty:
            return 0.0
        baseline = sensor_data.head(max(1, len(sensor_data) // 10)).mean()
        current = sensor_data.tail(max(1, len(sensor_data) // 10)).mean()
        deviation = np.abs((current - baseline) / (baseline.abs() + EPSILON)).mean()
        return float(np.clip(deviation, 0.0, 0.95))

    def _spectral_energy(self, values: np.ndarray) -> float:
        centered = values - np.mean(values)
        fft_values = np.fft.rfft(centered)
        return float(np.sum(np.square(np.abs(fft_values))) / max(len(values), 1))

    def _kurtosis(self, values: np.ndarray) -> float:
        if values.size < 4:
            return 3.0
        centered = values - np.mean(values)
        variance = np.mean(np.square(centered))
        if variance <= EPSILON:
            return 3.0
        fourth_moment = np.mean(np.power(centered, 4))
        kurt = fourth_moment / (variance**2)
        return float(kurt) if np.isfinite(kurt) else 3.0

    def _finite(self, value: float, fallback: float) -> float:
        return float(value) if np.isfinite(value) else float(fallback)
