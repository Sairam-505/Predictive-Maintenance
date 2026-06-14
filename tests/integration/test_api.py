from io import BytesIO

from fastapi.testclient import TestClient

from src.inference.api import app


client = TestClient(app)


def test_health_endpoint_reports_simulation_engine():
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["version"] == "2.0.0"
    assert payload["engine"] in {"simulation", "trained_models"}


def test_fleet_returns_eight_monitored_units():
    response = client.get("/fleet")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 8
    assert {"equipment_id", "equipment_type", "rul_hours", "alert_level"} <= set(payload[0])


def test_csv_upload_returns_prediction_without_random_stub():
    csv = b"vibration_x,vibration_y,temperature\n1.0,0.8,42\n2.0,1.5,44\n8.0,6.0,57\n"

    response = client.post(
        "/predict",
        files={"file": ("bearing_sample.csv", BytesIO(csv), "text/csv")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["equipment_type"] == "bearing"
    assert 0 < payload["rul_hours"] <= 500
    assert 0.78 <= payload["confidence_score"] <= 0.95
    assert payload["ai_explanation"]
