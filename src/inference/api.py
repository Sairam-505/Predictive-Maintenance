from __future__ import annotations

from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field

from src.inference.simulation import PhysicsSimulationEngine
from src.inference.store import EquipmentStore


app = FastAPI(title="Predictive Maintenance API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)

simulation_engine = PhysicsSimulationEngine()
equipment_store = EquipmentStore(simulation_engine=simulation_engine)
engine_mode = "simulation"
alerts_store: list[dict[str, Any]] = []

FLEET_BLUEPRINT = [
    ("BRG-101", "Bearing Press Line A", "bearing"),
    ("MTR-204", "Main Conveyor Motor", "motor"),
    ("PMP-017", "Cooling Pump 17", "pump"),
    ("GBX-332", "Gearbox Assembly 332", "gearbox"),
    ("TRB-055", "Turbine Cell 55", "turbine"),
    ("BRG-118", "Bearing Press Line B", "bearing"),
    ("MTR-311", "Auxiliary Motor 311", "motor"),
    ("PMP-044", "Hydraulic Pump 44", "pump"),
]


class EquipmentCreate(BaseModel):
    name: str = Field(..., min_length=1)
    equipment_type: str = Field(..., min_length=1)


class SensorReadingCreate(BaseModel):
    timestamp: str | None = None
    sensors: dict[str, float]


@app.on_event("startup")
def load_prediction_engine() -> None:
    global engine_mode
    model_dir = Path("models/final")
    if model_dir.exists() and any(model_dir.glob("*.pkl")):
        engine_mode = "trained_models"
    else:
        engine_mode = "simulation"


@app.get("/")
def read_root() -> dict[str, str]:
    return {"status": "healthy", "service": "Predictive Maintenance API", "version": "2.0.0"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "version": "2.0.0", "engine": engine_mode}


@app.post("/predict")
async def predict(file: UploadFile = File(...)) -> dict[str, Any]:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Upload a CSV file")

    try:
        raw = (await file.read()).decode("utf-8-sig")
        data = pd.read_csv(StringIO(raw))
        result = simulation_engine.analyze(data, equipment_id=file.filename.rsplit(".", 1)[0])
        result["ai_explanation"] = build_ai_explanation(result)
        result["source_file"] = file.filename
        return result
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/fleet")
def fleet() -> list[dict[str, Any]]:
    units = [build_fleet_unit(index, equipment) for index, equipment in enumerate(equipment_store.list_equipment())]
    refresh_alerts(units)
    return units


@app.post("/equipment")
def create_equipment(payload: EquipmentCreate) -> dict[str, Any]:
    equipment = equipment_store.create_equipment(payload.name, payload.equipment_type)
    status = equipment_store.analyze_equipment(equipment)
    return {"equipment": equipment, "status": status}


@app.get("/equipment")
def equipment_list() -> list[dict[str, Any]]:
    return fleet()


@app.get("/equipment/{equipment_id}")
def equipment_detail(equipment_id: str) -> dict[str, Any]:
    equipment = equipment_store.get_equipment(equipment_id)
    if equipment is None:
        raise HTTPException(status_code=404, detail="Equipment not found")

    unit = build_fleet_unit(0, equipment)
    history = equipment_store.build_history(equipment) or build_history(equipment_id, unit["rul_hours"])
    return {
        **unit,
        "history": history,
        "fault_probability": {
            "normal_degradation": max(0.1, unit["health_score"] / 100),
            "bearing_wear": 0.35 if unit["equipment_type"] == "bearing" else 0.12,
            "overheating": 0.18 if unit["alert_level"] != "healthy" else 0.05,
            "flow_instability": 0.3 if unit["equipment_type"] == "pump" else 0.08,
        },
        "maintenance_history": [
            {"date": "2026-05-04", "event": "Routine vibration inspection completed"},
            {"date": "2026-05-22", "event": "Lubrication and thermal scan completed"},
            {"date": "2026-06-10", "event": "Automated health check recorded"},
        ],
    }


@app.post("/equipment/{equipment_id}/readings")
def add_sensor_reading(equipment_id: str, payload: SensorReadingCreate) -> dict[str, Any]:
    try:
        result = equipment_store.add_reading(equipment_id, payload.sensors, payload.timestamp)
        refresh_alerts(fleet())
        return result
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Equipment not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/alerts")
def alerts() -> list[dict[str, Any]]:
    if not alerts_store:
        refresh_alerts(fleet())
    return sorted(alerts_store, key=lambda item: item["rul_hours"])


@app.post("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: str) -> dict[str, Any]:
    if not alerts_store:
        refresh_alerts(fleet())
    for alert in alerts_store:
        if alert["id"] == alert_id:
            alert["acknowledged"] = True
            return alert
    raise HTTPException(status_code=404, detail="Alert not found")


@app.get("/report")
def report() -> list[dict[str, Any]]:
    rows = []
    for unit in fleet():
        next_maintenance = datetime.now(timezone.utc) + timedelta(hours=max(unit["rul_hours"] * 0.75, 1))
        rows.append(
            {
                "equipment_id": unit["equipment_id"],
                "name": unit["name"],
                "equipment_type": unit["equipment_type"],
                "current_rul_hours": unit["rul_hours"],
                "health_score": unit["health_score"],
                "alert_level": unit["alert_level"],
                "last_maintenance_date": "2026-05-22",
                "recommended_next_maintenance": next_maintenance.date().isoformat(),
            }
        )
    return sorted(rows, key=lambda item: item["current_rul_hours"])


def build_fleet_unit(index: int, equipment: dict[str, Any]) -> dict[str, Any]:
    equipment_id = equipment["equipment_id"]
    if equipment.get("readings"):
        result = equipment_store.analyze_equipment(equipment)
    elif equipment.get("is_demo", False):
        synthetic_data = synthetic_sensor_frame(equipment["equipment_type"], index)
        result = simulation_engine.analyze(synthetic_data, equipment_id=equipment_id)
    else:
        result = equipment_store.analyze_equipment(equipment)
    return {
        "equipment_id": equipment_id,
        "name": equipment["name"],
        "equipment_type": equipment["equipment_type"],
        "rul_hours": result["rul_hours"],
        "health_score": result["health_score"],
        "alert_level": result["alert_level"],
        "fault_type": result["fault_type"],
        "confidence_score": result["confidence_score"],
        "reading_count": result.get("reading_count", len(equipment.get("readings", []))),
        "last_updated": result.get("last_updated", equipment["last_updated"]),
    }


def synthetic_sensor_frame(equipment_type: str, index: int) -> pd.DataFrame:
    size = 512
    x = pd.Series(range(size), dtype="float64")
    severity = 0.25 + (index % 4) * 0.25

    if equipment_type == "bearing":
        return pd.DataFrame(
            {
                "vibration_x": (x / 18).map(lambda value: severity * 6.0 * __import__("math").sin(value)),
                "vibration_y": (x / 21).map(lambda value: severity * 4.0 * __import__("math").cos(value)),
                "temperature": 42 + severity * x / 30,
            }
        )
    if equipment_type == "motor":
        return pd.DataFrame({"stator_current": 3.0 + severity * x / 80, "motor_temperature": 45 + severity * x / 35})
    if equipment_type == "pump":
        return pd.DataFrame({"pressure": 95 - severity * x / 18, "flow": 72 - severity * x / 25, "temperature": 40 + severity * x / 60})
    if equipment_type == "gearbox":
        return pd.DataFrame({"gear_vibration": severity * 8.0 * (x / 15).map(lambda value: __import__("math").sin(value)), "torque": 140 + severity * x / 20})
    if equipment_type == "turbine":
        data = {"cycle": x}
        for sensor_id in range(1, 6):
            data[f"sensor_{sensor_id}"] = 0.5 + severity * sensor_id * x / 3500
        return pd.DataFrame(data)
    return pd.DataFrame({"sensor_value": severity * x / 50})


def refresh_alerts(units: list[dict[str, Any]]) -> None:
    existing_ack = {alert["equipment_id"]: alert.get("acknowledged", False) for alert in alerts_store}
    alerts_store.clear()
    for unit in units:
        if unit["alert_level"] == "healthy":
            continue
        severity = "CRITICAL" if unit["alert_level"] == "critical" else "WARNING"
        alerts_store.append(
            {
                "id": f"ALT-{unit['equipment_id']}",
                "equipment_id": unit["equipment_id"],
                "equipment_name": unit["name"],
                "severity": severity,
                "fault_type": unit["fault_type"],
                "rul_hours": unit["rul_hours"],
                "timestamp": unit["last_updated"],
                "acknowledged": existing_ack.get(unit["equipment_id"], False),
            }
        )


def build_history(equipment_id: str, current_rul: float) -> list[dict[str, Any]]:
    seed = sum(ord(char) for char in equipment_id)
    history = []
    start = datetime.now(timezone.utc) - timedelta(days=7)
    for hour in range(7 * 24):
        degradation = (7 * 24 - hour) * ((seed % 5) + 1) * 0.12
        rul = max(1.0, current_rul + degradation)
        history.append(
            {
                "timestamp": (start + timedelta(hours=hour)).isoformat(),
                "rul": round(rul, 2),
                "vibration_rms": round(1.8 + (seed % 7) * 0.2 + hour * 0.01, 3),
                "temperature": round(39 + (seed % 9) + hour * 0.025, 2),
                "kurtosis": round(3.0 + (seed % 4) * 0.3 + hour * 0.004, 3),
            }
        )
    return history


def build_ai_explanation(result: dict[str, Any]) -> str:
    stats = result["sensor_statistics"]
    return (
        f"The uploaded sensor profile was classified as {result['equipment_type']} with "
        f"{result['confidence_score']:.0%} confidence. RMS is {stats['rms']} and kurtosis is "
        f"{stats['kurtosis']}, indicating {result['fault_type'].replace('_', ' ')}. "
        f"Estimated remaining useful life is {result['rul_hours']} hours. "
        f"{result['recommendation']}"
    )
