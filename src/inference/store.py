from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd

from src.inference.simulation import PhysicsSimulationEngine


DEFAULT_EQUIPMENT = [
    ("BRG-101", "Bearing Press Line A", "bearing"),
    ("MTR-204", "Main Conveyor Motor", "motor"),
    ("PMP-017", "Cooling Pump 17", "pump"),
    ("GBX-332", "Gearbox Assembly 332", "gearbox"),
    ("TRB-055", "Turbine Cell 55", "turbine"),
    ("BRG-118", "Bearing Press Line B", "bearing"),
    ("MTR-311", "Auxiliary Motor 311", "motor"),
    ("PMP-044", "Hydraulic Pump 44", "pump"),
]


class EquipmentStore:
    """JSON-backed store for user equipment and sensor readings."""

    def __init__(
        self,
        path: str | Path = "runtime_data/equipment_store.json",
        simulation_engine: PhysicsSimulationEngine | None = None,
    ):
        self.path = Path(path)
        self.simulation_engine = simulation_engine or PhysicsSimulationEngine()
        self.state = self._load()

    def list_equipment(self) -> list[dict[str, Any]]:
        return list(self.state["equipment"].values())

    def get_equipment(self, equipment_id: str) -> dict[str, Any] | None:
        return self.state["equipment"].get(equipment_id)

    def create_equipment(self, name: str, equipment_type: str) -> dict[str, Any]:
        equipment_type = equipment_type.lower().strip() or "default"
        prefix = equipment_type[:3].upper()
        equipment_id = f"{prefix}-{uuid4().hex[:6].upper()}"
        now = self._now()
        equipment = {
            "equipment_id": equipment_id,
            "name": name.strip(),
            "equipment_type": equipment_type,
            "is_demo": False,
            "created_at": now,
            "last_updated": now,
            "readings": [],
        }
        self.state["equipment"][equipment_id] = equipment
        self._save()
        return equipment

    def add_reading(
        self,
        equipment_id: str,
        sensors: dict[str, float],
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        equipment = self.get_equipment(equipment_id)
        if equipment is None:
            raise KeyError(equipment_id)

        clean_sensors = {key: float(value) for key, value in sensors.items() if value is not None}
        if not clean_sensors:
            raise ValueError("At least one sensor value is required")

        reading = {
            "timestamp": timestamp or self._now(),
            "sensors": clean_sensors,
        }
        equipment["readings"].append(reading)
        equipment["last_updated"] = reading["timestamp"]
        result = self.analyze_equipment(equipment)
        reading["result"] = {
            "rul_hours": result["rul_hours"],
            "health_score": result["health_score"],
            "alert_level": result["alert_level"],
            "fault_type": result["fault_type"],
            "confidence_score": result["confidence_score"],
        }
        self._save()
        return {"equipment": equipment, "reading": reading, "status": result}

    def analyze_equipment(self, equipment: dict[str, Any]) -> dict[str, Any]:
        readings = equipment.get("readings", [])
        if readings:
            frame = pd.DataFrame([item["sensors"] for item in readings])
            frame = self._with_equipment_hint(frame, equipment["equipment_type"])
            result = self.simulation_engine.analyze(frame, equipment_id=equipment["equipment_id"])
        else:
            result = self._empty_status(equipment)

        result["equipment_id"] = equipment["equipment_id"]
        result["name"] = equipment["name"]
        result["equipment_type"] = equipment["equipment_type"]
        result["reading_count"] = len(readings)
        result["last_updated"] = equipment["last_updated"]
        result["status_message"] = self._status_message(result)
        return result

    def build_history(self, equipment: dict[str, Any]) -> list[dict[str, Any]]:
        readings = equipment.get("readings", [])
        if not readings:
            return []

        history = []
        for index, reading in enumerate(readings):
            sensors = reading["sensors"]
            partial = {
                "equipment_id": equipment["equipment_id"],
                "equipment_type": equipment["equipment_type"],
                "timestamp": reading["timestamp"],
                "rul": reading.get("result", {}).get("rul_hours"),
                "vibration_rms": sensors.get("vibration", sensors.get("vibration_x", sensors.get("gear_vibration", 0))),
                "temperature": sensors.get("temperature", sensors.get("motor_temperature", 0)),
                "kurtosis": sensors.get("kurtosis", 3.0),
                "reading_index": index + 1,
                **sensors,
            }
            if partial["rul"] is None:
                result = self.analyze_equipment({"equipment_id": equipment["equipment_id"], "name": equipment["name"], "equipment_type": equipment["equipment_type"], "last_updated": reading["timestamp"], "readings": readings[: index + 1]})
                partial["rul"] = result["rul_hours"]
            history.append(partial)
        return history

    def _load(self) -> dict[str, Any]:
        if self.path.exists():
            with open(self.path, "r", encoding="utf-8") as file:
                state = json.load(file)
            for equipment_id, equipment in state.get("equipment", {}).items():
                equipment.setdefault("is_demo", equipment_id in {item[0] for item in DEFAULT_EQUIPMENT})
                equipment.setdefault("readings", [])
            return state

        now = self._now()
        equipment = {
            equipment_id: {
                "equipment_id": equipment_id,
                "name": name,
                "equipment_type": equipment_type,
                "is_demo": True,
                "created_at": now,
                "last_updated": now,
                "readings": [],
            }
            for equipment_id, name, equipment_type in DEFAULT_EQUIPMENT
        }
        return {"equipment": equipment}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as file:
            json.dump(self.state, file, indent=2)

    def _with_equipment_hint(self, frame: pd.DataFrame, equipment_type: str) -> pd.DataFrame:
        frame = frame.copy()
        if equipment_type == "bearing" and not any("vibration" in col for col in frame.columns):
            frame = frame.rename(columns={frame.columns[0]: "vibration"})
        if equipment_type == "motor" and not any("current" in col or "motor" in col for col in frame.columns):
            frame = frame.rename(columns={frame.columns[0]: "stator_current"})
        if equipment_type == "pump" and not any("pressure" in col or "flow" in col for col in frame.columns):
            frame = frame.rename(columns={frame.columns[0]: "pressure"})
        if equipment_type == "gearbox" and not any("gear" in col or "torque" in col for col in frame.columns):
            frame = frame.rename(columns={frame.columns[0]: "gear_vibration"})
        if equipment_type == "turbine" and not any(str(col).startswith("sensor_") for col in frame.columns):
            frame = frame.rename(columns={frame.columns[0]: "sensor_1"})
        return frame

    def _empty_status(self, equipment: dict[str, Any]) -> dict[str, Any]:
        base_rul = self.simulation_engine.BASE_RUL.get(equipment["equipment_type"], 300.0)
        return {
            "equipment_id": equipment["equipment_id"],
            "equipment_type": equipment["equipment_type"],
            "predicted_rul_hours": base_rul,
            "rul_hours": base_rul,
            "confidence_score": 0.78,
            "fault_type": "awaiting_sensor_readings",
            "alert_level": "healthy",
            "health_score": 100,
            "recommendation": "Add sensor readings to begin tracking degradation and RUL.",
            "sensor_statistics": {},
            "engine": "simulation",
        }

    def _status_message(self, result: dict[str, Any]) -> str:
        if result["reading_count"] < 3:
            return "Reading saved. Add more readings over time for a stronger RUL trend."
        if result["alert_level"] == "critical":
            return "Critical health status. Schedule immediate maintenance inspection."
        if result["alert_level"] == "warning":
            return "Warning health status. Plan maintenance and keep entering readings."
        return "Healthy status. Reading saved and RUL trend updated."

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()
