export type AlertLevel = "healthy" | "warning" | "critical";
export type Severity = "CRITICAL" | "WARNING" | "INFO";

export interface FleetUnit {
  equipment_id: string;
  name: string;
  equipment_type: string;
  rul_hours: number;
  health_score: number;
  alert_level: AlertLevel;
  fault_type: string;
  confidence_score: number;
  last_updated: string;
}

export interface AlertItem {
  id: string;
  equipment_id: string;
  equipment_name: string;
  severity: Severity;
  fault_type: string;
  rul_hours: number;
  timestamp: string;
  acknowledged: boolean;
}

export interface HistoryPoint {
  timestamp: string;
  rul: number;
  vibration_rms: number;
  temperature: number;
  kurtosis: number;
}

export interface EquipmentDetail extends FleetUnit {
  history: HistoryPoint[];
  fault_probability: Record<string, number>;
  maintenance_history: Array<{ date: string; event: string }>;
}

export interface ReportRow {
  equipment_id: string;
  name: string;
  equipment_type: string;
  current_rul_hours: number;
  health_score: number;
  alert_level: AlertLevel;
  last_maintenance_date: string;
  recommended_next_maintenance: string;
}

export interface PredictionResult {
  equipment_id: string;
  equipment_type: string;
  rul_hours: number;
  predicted_rul_hours: number;
  confidence_score: number;
  fault_type: string;
  alert_level: AlertLevel;
  health_score: number;
  recommendation: string;
  ai_explanation: string;
  sensor_statistics: Record<string, number>;
}
