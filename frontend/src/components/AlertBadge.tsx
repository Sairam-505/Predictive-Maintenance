import type { AlertLevel, Severity } from "../types";

const labels: Record<string, string> = {
  healthy: "INFO",
  warning: "WARNING",
  critical: "CRITICAL"
};

export default function AlertBadge({ value }: { value: AlertLevel | Severity }) {
  const normalized = value.toLowerCase();
  return <span className={`alert-badge ${normalized}`}>{labels[normalized] ?? value}</span>;
}
