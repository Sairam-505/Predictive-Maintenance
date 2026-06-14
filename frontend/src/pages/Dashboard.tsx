import { useCallback, useMemo, useState } from "react";
import { getFleet } from "../api/client";
import RULCard from "../components/RULCard";
import SensorChart from "../components/SensorChart";
import { usePolling } from "../hooks/usePolling";

const filters = ["all", "bearing", "motor", "pump", "gearbox"];

export default function Dashboard() {
  const [filter, setFilter] = useState("all");
  const loadFleet = useCallback(() => getFleet(), []);
  const { data, loading, error } = usePolling(loadFleet, 30000);
  const units = data ?? [];
  const filtered = filter === "all" ? units : units.filter((unit) => unit.equipment_type === filter);
  const trend = useMemo(
    () => units.map((unit, index) => ({ timestamp: unit.equipment_id, value: Math.round(unit.rul_hours), index })),
    [units]
  );

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
      {loading ? <div className="skeleton-grid" /> : <div className="fleet-grid">{filtered.map((unit) => <RULCard key={unit.equipment_id} unit={unit} />)}</div>}
      <section className="panel">
        <h2>Fleet RUL Trend</h2>
        <SensorChart data={trend} dataKey="value" />
      </section>
    </section>
  );
}
