import { ArrowRight, Cpu, Gauge, RadioTower, ShieldCheck } from "lucide-react";
import { Link } from "react-router-dom";

const equipment = ["Bearings", "Motors", "Pumps", "Gearboxes", "Turbines", "Compressors", "Fans", "Conveyors", "Hydraulics", "CNC Tools"];

export default function Landing() {
  return (
    <section className="landing">
      <div className="hero-band">
        <div className="hero-copy">
          <p>Universal Predictive Maintenance</p>
          <h1>Maintenance Driven by Prediction, Not Reaction.</h1>
          <Link to="/dashboard" className="primary hero-cta">Open Dashboard <ArrowRight size={18} /></Link>
        </div>
        <div className="digital-twin">
          <div className="motor-core" />
          <div className="telemetry-card one"><Gauge size={16} /> RUL 142h</div>
          <div className="telemetry-card two"><RadioTower size={16} /> 8 live units</div>
          <div className="telemetry-card three"><ShieldCheck size={16} /> Risk ranked</div>
        </div>
      </div>
      <section className="equipment-strip">
        {equipment.map((item) => <span key={item}><Cpu size={14} />{item}</span>)}
      </section>
      <section className="pipeline-row">
        <article><b>01</b><h2>Sensor Upload</h2><p>CSV vibration, pressure, current, thermal, and cycle data.</p></article>
        <article><b>02</b><h2>Physics Engine</h2><p>Equipment detection, fault signature analysis, and RUL scoring.</p></article>
        <article><b>03</b><h2>Maintenance Action</h2><p>Alerts, reports, recommendations, and downloadable schedules.</p></article>
      </section>
    </section>
  );
}
