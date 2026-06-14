import { Activity, Gauge, Wrench } from "lucide-react";
import { Link } from "react-router-dom";
import type { FleetUnit } from "../types";
import AlertBadge from "./AlertBadge";

export default function RULCard({ unit }: { unit: FleetUnit }) {
  return (
    <Link className="rul-card" to={`/equipment/${unit.equipment_id}`}>
      <div className="card-topline">
        <span className="equipment-icon"><Gauge size={18} /></span>
        <AlertBadge value={unit.alert_level} />
      </div>
      <div>
        <h3>{unit.name}</h3>
        <p>{unit.equipment_id} · {unit.equipment_type}</p>
      </div>
      <div className="rul-value">{Math.round(unit.rul_hours)}h</div>
      <div className="health-bar" aria-label="Health score">
        <span style={{ width: `${unit.health_score}%` }} />
      </div>
      <div className="card-footer">
        <span><Activity size={14} /> {unit.fault_type.replaceAll("_", " ")}</span>
        <span><Wrench size={14} /> {unit.health_score}% · {unit.reading_count ?? 0} readings</span>
      </div>
    </Link>
  );
}
