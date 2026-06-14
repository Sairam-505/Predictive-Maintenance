import { useCallback, useState } from "react";
import { acknowledgeAlert, getAlerts } from "../api/client";
import AlertBadge from "../components/AlertBadge";
import { usePolling } from "../hooks/usePolling";

export default function Alerts() {
  const [confirmId, setConfirmId] = useState<string | null>(null);
  const loadAlerts = useCallback(() => getAlerts(), []);
  const { data, loading, error } = usePolling(loadAlerts, 30000);

  async function acknowledge(id: string) {
    await acknowledgeAlert(id);
    setConfirmId(null);
    window.location.reload();
  }

  return (
    <section className="page">
      <header className="page-header">
        <div>
          <p>Operations Queue</p>
          <h1>Active Alerts</h1>
        </div>
      </header>
      {error && <button className="error-banner" onClick={() => window.location.reload()}>Alert feed unavailable. Retry</button>}
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Severity</th>
              <th>Equipment</th>
              <th>Fault</th>
              <th>RUL</th>
              <th>Timestamp</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {loading && <tr><td colSpan={6}>Loading alerts...</td></tr>}
            {(data ?? []).map((alert) => (
              <tr key={alert.id}>
                <td><AlertBadge value={alert.severity} /></td>
                <td>{alert.equipment_name}</td>
                <td>{alert.fault_type.replaceAll("_", " ")}</td>
                <td className="mono">{Math.round(alert.rul_hours)}h</td>
                <td>{new Date(alert.timestamp).toLocaleString()}</td>
                <td>
                  {alert.acknowledged ? "Acknowledged" : <button className="table-action" onClick={() => setConfirmId(alert.id)}>Acknowledge</button>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {confirmId && (
        <div className="modal-backdrop">
          <div className="modal">
            <h2>Acknowledge alert?</h2>
            <p>This records the alert as seen by maintenance operations.</p>
            <div>
              <button onClick={() => setConfirmId(null)}>Cancel</button>
              <button className="primary" onClick={() => acknowledge(confirmId)}>Acknowledge</button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
