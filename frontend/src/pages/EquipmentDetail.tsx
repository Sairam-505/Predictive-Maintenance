import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getEquipment } from "../api/client";
import AlertBadge from "../components/AlertBadge";
import SensorChart from "../components/SensorChart";
import type { EquipmentDetail as EquipmentDetailType } from "../types";

export default function EquipmentDetail() {
  const { id = "" } = useParams();
  const [data, setData] = useState<EquipmentDetailType | null>(null);
  const [error, setError] = useState(false);
  const load = useCallback(async () => {
    try {
      setError(false);
      setData(await getEquipment(id));
    } catch {
      setError(true);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  if (error) return <button className="error-banner" onClick={load}>Equipment unavailable. Retry</button>;
  if (!data) return <section className="page"><div className="skeleton-grid" /></section>;

  return (
    <section className="page">
      <header className="page-header detail-header">
        <div>
          <p>{data.equipment_id}</p>
          <h1>{data.name}</h1>
        </div>
        <AlertBadge value={data.alert_level} />
      </header>
      <div className="detail-grid">
        <section className="panel">
          <h2>7-Day Sensor Trend</h2>
          <SensorChart data={data.history} dataKey="rul" height={340} />
        </section>
        <section className="panel metric-panel">
          <h2>Health Score</h2>
          <div className="gauge">{data.health_score}%</div>
          <p className="mono">{Math.round(data.rul_hours)}h RUL</p>
          {Object.entries(data.fault_probability).map(([name, value]) => (
            <div className="prob-row" key={name}>
              <span>{name.replaceAll("_", " ")}</span>
              <b>{Math.round(value * 100)}%</b>
            </div>
          ))}
        </section>
      </div>
      <section className="panel">
        <h2>Maintenance History</h2>
        <div className="timeline">
          {data.maintenance_history.map((item) => <p key={item.date}><b>{item.date}</b>{item.event}</p>)}
        </div>
      </section>
    </section>
  );
}
