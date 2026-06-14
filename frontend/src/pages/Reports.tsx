import { useCallback } from "react";
import { getReport } from "../api/client";
import AlertBadge from "../components/AlertBadge";
import { usePolling } from "../hooks/usePolling";
import type { ReportRow } from "../types";

export default function Reports() {
  const loadReport = useCallback(() => getReport(), []);
  const { data, loading, error } = usePolling(loadReport, 30000);
  const rows = [...(data ?? [])].sort((a, b) => a.current_rul_hours - b.current_rul_hours);

  function downloadCsv() {
    const csv = toCsv(rows);
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = "fleet-maintenance-report.csv";
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <section className="page">
      <header className="page-header">
        <div>
          <p>Maintenance Plan</p>
          <h1>Fleet Reports</h1>
        </div>
        <button className="primary" onClick={downloadCsv} disabled={!rows.length}>Download CSV</button>
      </header>
      {error && <button className="error-banner" onClick={() => window.location.reload()}>Report unavailable. Retry</button>}
      <div className="table-wrap print-friendly">
        <table>
          <thead>
            <tr>
              <th>Equipment</th>
              <th>Type</th>
              <th>RUL</th>
              <th>Health</th>
              <th>Alert</th>
              <th>Last Maintenance</th>
              <th>Next Maintenance</th>
            </tr>
          </thead>
          <tbody>
            {loading && <tr><td colSpan={7}>Loading report...</td></tr>}
            {rows.map((row) => (
              <tr key={row.equipment_id}>
                <td>{row.name}</td>
                <td>{row.equipment_type}</td>
                <td className="mono">{Math.round(row.current_rul_hours)}h</td>
                <td>{row.health_score}%</td>
                <td><AlertBadge value={row.alert_level} /></td>
                <td>{row.last_maintenance_date}</td>
                <td>{row.recommended_next_maintenance}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function toCsv(rows: ReportRow[]) {
  const header = Object.keys(rows[0] ?? {});
  const body = rows.map((row) => header.map((key) => JSON.stringify(row[key as keyof ReportRow] ?? "")).join(","));
  return [header.join(","), ...body].join("\n");
}
