import { FormEvent, useCallback, useMemo, useState } from "react";
import { addSensorReading, createEquipment, getFleet } from "../api/client";
import AlertBadge from "../components/AlertBadge";
import RULCard from "../components/RULCard";
import SensorChart from "../components/SensorChart";
import { usePolling } from "../hooks/usePolling";
import type { ReadingStatusResponse } from "../types";

const filters = ["all", "bearing", "motor", "pump", "gearbox"];
const equipmentTypes = ["bearing", "motor", "pump", "gearbox", "turbine", "default"];

export default function Dashboard() {
  const [filter, setFilter] = useState("all");
  const [refreshKey, setRefreshKey] = useState(0);
  const [newEquipment, setNewEquipment] = useState({ name: "", equipment_type: "bearing" });
  const [readingEquipmentId, setReadingEquipmentId] = useState("");
  const [readingValues, setReadingValues] = useState({
    vibration: "",
    temperature: "",
    pressure: "",
    flow: "",
    current: "",
    torque: ""
  });
  const [statusPopup, setStatusPopup] = useState<ReadingStatusResponse | null>(null);
  const [formError, setFormError] = useState("");
  const loadFleet = useCallback(() => getFleet(), [refreshKey]);
  const { data, loading, error } = usePolling(loadFleet, 30000);
  const units = data ?? [];
  const filtered = filter === "all" ? units : units.filter((unit) => unit.equipment_type === filter);
  const trend = useMemo(
    () => units.map((unit, index) => ({ timestamp: unit.equipment_id, value: Math.round(unit.rul_hours), index })),
    [units]
  );
  const selectedEquipmentId = readingEquipmentId || units[0]?.equipment_id || "";

  async function submitEquipment(event: FormEvent) {
    event.preventDefault();
    setFormError("");
    if (!newEquipment.name.trim()) {
      setFormError("Enter an equipment name.");
      return;
    }
    await createEquipment(newEquipment);
    setNewEquipment({ name: "", equipment_type: "bearing" });
    setRefreshKey((value) => value + 1);
  }

  async function submitReading(event: FormEvent) {
    event.preventDefault();
    setFormError("");
    const sensors = Object.fromEntries(
      Object.entries(readingValues)
        .filter(([, value]) => value.trim() !== "")
        .map(([key, value]) => [key, Number(value)])
        .filter(([, value]) => Number.isFinite(value))
    );
    if (!selectedEquipmentId) {
      setFormError("Add or select equipment first.");
      return;
    }
    if (!Object.keys(sensors).length) {
      setFormError("Enter at least one sensor value.");
      return;
    }
    const response = await addSensorReading(selectedEquipmentId, { sensors });
    setStatusPopup(response);
    setReadingValues({ vibration: "", temperature: "", pressure: "", flow: "", current: "", torque: "" });
    setRefreshKey((value) => value + 1);
  }

  return (
    <section className="page">
      <header className="page-header">
        <div>
          <p>Fleet Command</p>
          <h1>Predictive Maintenance Dashboard</h1>
        </div>
      </header>
      <div className="filter-row">
        {filters.map((item) => (
          <button key={item} className={filter === item ? "chip active" : "chip"} onClick={() => setFilter(item)}>
            {item}
          </button>
        ))}
      </div>
      {error && <button className="error-banner" onClick={() => window.location.reload()}>API unavailable. Retry</button>}
      {formError && <div className="error-banner">{formError}</div>}
      <div className="operations-grid">
        <form className="panel compact-form" onSubmit={submitEquipment}>
          <h2>Add Equipment</h2>
          <label>
            Equipment name
            <input value={newEquipment.name} onChange={(event) => setNewEquipment({ ...newEquipment, name: event.target.value })} placeholder="Boiler feed pump" />
          </label>
          <label>
            Equipment type
            <select value={newEquipment.equipment_type} onChange={(event) => setNewEquipment({ ...newEquipment, equipment_type: event.target.value })}>
              {equipmentTypes.map((type) => <option key={type} value={type}>{type}</option>)}
            </select>
          </label>
          <button className="primary" type="submit">Add Equipment</button>
        </form>
        <form className="panel compact-form" onSubmit={submitReading}>
          <h2>Enter Sensor Reading</h2>
          <label>
            Equipment
            <select value={selectedEquipmentId} onChange={(event) => setReadingEquipmentId(event.target.value)}>
              {units.map((unit) => <option key={unit.equipment_id} value={unit.equipment_id}>{unit.name} ({unit.equipment_id})</option>)}
            </select>
          </label>
          <div className="sensor-input-grid">
            {Object.entries(readingValues).map(([key, value]) => (
              <label key={key}>
                {key}
                <input type="number" step="0.01" value={value} onChange={(event) => setReadingValues({ ...readingValues, [key]: event.target.value })} />
              </label>
            ))}
          </div>
          <button className="primary" type="submit">Save Reading & Check Health</button>
        </form>
      </div>
      {loading ? <div className="skeleton-grid" /> : <div className="fleet-grid">{filtered.map((unit) => <RULCard key={unit.equipment_id} unit={unit} />)}</div>}
      <section className="panel">
        <h2>Fleet RUL Trend</h2>
        <SensorChart data={trend} dataKey="value" />
      </section>
      {statusPopup && (
        <div className="modal-backdrop">
          <div className="modal status-modal">
            <AlertBadge value={statusPopup.status.alert_level} />
            <h2>{statusPopup.status.name}</h2>
            <div className="status-rul">{Math.round(statusPopup.status.rul_hours)}h RUL</div>
            <p>{statusPopup.status.status_message}</p>
            <p>{statusPopup.status.recommendation}</p>
            <div className="prob-row">
              <span>Health</span>
              <b>{statusPopup.status.health_score}%</b>
            </div>
            <div className="prob-row">
              <span>Readings recorded</span>
              <b>{statusPopup.status.reading_count}</b>
            </div>
            <div>
              <button className="primary" onClick={() => setStatusPopup(null)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
