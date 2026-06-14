import { Activity, Bell, FileBarChart, Gauge, Home, UploadCloud } from "lucide-react";
import { NavLink } from "react-router-dom";
import { getAlerts } from "../api/client";
import { usePolling } from "../hooks/usePolling";

const links = [
  { to: "/", label: "Overview", icon: Home },
  { to: "/dashboard", label: "Dashboard", icon: Gauge },
  { to: "/analyze", label: "Analyse", icon: UploadCloud },
  { to: "/alerts", label: "Alerts", icon: Bell },
  { to: "/reports", label: "Reports", icon: FileBarChart }
];

export default function NavBar() {
  const { data } = usePolling(getAlerts, 30000);
  const alertCount = data?.filter((alert) => !alert.acknowledged).length ?? 0;

  return (
    <aside className="nav-shell">
      <div className="brand-mark">
        <Activity size={24} />
        <span>PredMaint</span>
      </div>
      <nav>
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink key={to} to={to} className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}>
            <Icon size={18} />
            <span>{label}</span>
            {label === "Alerts" && alertCount > 0 && <b>{alertCount}</b>}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
