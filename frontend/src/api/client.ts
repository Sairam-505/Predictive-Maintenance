import axios from "axios";
import type {
  AlertItem,
  EquipmentCreatePayload,
  EquipmentDetail,
  FleetUnit,
  PredictionResult,
  ReadingStatusResponse,
  ReportRow,
  SensorReadingPayload
} from "../types";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
  timeout: 15000
});

const STORAGE_KEY = "predictive-maintenance-demo-equipment";

const demoFleet: FleetUnit[] = [
  unit("BRG-101", "Bearing Press Line A", "bearing", 42, 8),
  unit("MTR-204", "Main Conveyor Motor", "motor", 360, 0),
  unit("PMP-017", "Cooling Pump 17", "pump", 118, 3),
  unit("GBX-332", "Gearbox Assembly 332", "gearbox", 76, 5),
  unit("TRB-055", "Turbine Cell 55", "turbine", 210, 2),
  unit("BRG-118", "Bearing Press Line B", "bearing", 18, 9),
  unit("MTR-311", "Auxiliary Motor 311", "motor", 640, 0),
  unit("PMP-044", "Hydraulic Pump 44", "pump", 145, 4)
];

export async function getFleet() {
  try {
    const response = await api.get<FleetUnit[]>("/fleet");
    return response.data;
  } catch {
    return offlineFleet();
  }
}

export async function getAlerts() {
  try {
    const response = await api.get<AlertItem[]>("/alerts");
    return response.data;
  } catch {
    return offlineAlerts();
  }
}

export async function acknowledgeAlert(id: string) {
  try {
    const response = await api.post<AlertItem>(`/alerts/${id}/acknowledge`);
    return response.data;
  } catch {
    const alerts = offlineAlerts();
    return alerts.find((alert) => alert.id === id) ?? alerts[0];
  }
}

export async function getEquipment(id: string) {
  try {
    const response = await api.get<EquipmentDetail>(`/equipment/${id}`);
    return response.data;
  } catch {
    return offlineEquipment(id);
  }
}

export async function createEquipment(payload: EquipmentCreatePayload) {
  try {
    const response = await api.post<{ equipment: unknown; status: FleetUnit }>("/equipment", payload);
    return response.data;
  } catch {
    const next = unit(
      `${payload.equipment_type.slice(0, 3).toUpperCase()}-${Math.random().toString(16).slice(2, 8).toUpperCase()}`,
      payload.name,
      payload.equipment_type,
      baseRul(payload.equipment_type),
      0
    );
    saveOfflineFleet([...offlineFleet(), next]);
    return { equipment: next, status: next };
  }
}

export async function addSensorReading(equipmentId: string, payload: SensorReadingPayload) {
  try {
    const response = await api.post<ReadingStatusResponse>(`/equipment/${equipmentId}/readings`, payload);
    return response.data;
  } catch {
    return saveOfflineReading(equipmentId, payload.sensors);
  }
}

export async function getReport() {
  try {
    const response = await api.get<ReportRow[]>("/report");
    return response.data;
  } catch {
    return offlineFleet().map((item) => ({
      equipment_id: item.equipment_id,
      name: item.name,
      equipment_type: item.equipment_type,
      current_rul_hours: item.rul_hours,
      health_score: item.health_score,
      alert_level: item.alert_level,
      last_maintenance_date: "2026-05-22",
      recommended_next_maintenance: new Date(Date.now() + item.rul_hours * 2700000).toISOString().slice(0, 10)
    }));
  }
}

export async function uploadCsv(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post<PredictionResult>("/predict", formData, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return response.data;
}

function unit(equipment_id: string, name: string, equipment_type: string, rul_hours: number, reading_count: number): FleetUnit {
  const health_score = Math.max(1, Math.min(100, Math.round((rul_hours / baseRul(equipment_type)) * 100)));
  return {
    equipment_id,
    name,
    equipment_type,
    rul_hours,
    health_score,
    alert_level: rul_hours < 24 ? "critical" : rul_hours < 168 ? "warning" : "healthy",
    fault_type: reading_count ? "normal_degradation" : "awaiting_sensor_readings",
    confidence_score: reading_count ? 0.86 : 0.78,
    reading_count,
    last_updated: new Date().toISOString()
  };
}

function offlineFleet(): FleetUnit[] {
  const saved = window.localStorage.getItem(STORAGE_KEY);
  if (!saved) {
    saveOfflineFleet(demoFleet);
    return demoFleet;
  }
  return JSON.parse(saved) as FleetUnit[];
}

function saveOfflineFleet(fleet: FleetUnit[]) {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(fleet));
}

function saveOfflineReading(equipmentId: string, sensors: Record<string, number>): ReadingStatusResponse {
  const fleet = offlineFleet();
  const index = fleet.findIndex((item) => item.equipment_id === equipmentId);
  const current = fleet[index] ?? demoFleet[0];
  const severity = Object.values(sensors).reduce((sum, value) => sum + Math.abs(Number(value) || 0), 0) / Math.max(1, Object.keys(sensors).length);
  const nextCount = current.reading_count + 1;
  const degradation = Math.min(baseRul(current.equipment_type) * 0.22, severity * 2.4 + nextCount * 4);
  const next = unit(current.equipment_id, current.name, current.equipment_type, Math.max(1, current.rul_hours - degradation), nextCount);
  fleet[index] = next;
  saveOfflineFleet(fleet);
  return {
    equipment: { ...next, readings: [] },
    reading: { timestamp: new Date().toISOString(), sensors },
    status: {
      ...next,
      recommendation: next.alert_level === "critical" ? "Schedule immediate inspection." : next.alert_level === "warning" ? "Plan maintenance and continue logging readings." : "Continue normal monitoring.",
      status_message: next.reading_count < 3 ? "Reading saved. Add more readings for a stronger RUL trend." : "Reading saved and health trend updated.",
      sensor_statistics: sensors
    }
  };
}

function offlineAlerts(): AlertItem[] {
  return offlineFleet()
    .filter((item) => item.alert_level !== "healthy")
    .sort((a, b) => a.rul_hours - b.rul_hours)
    .map((item) => ({
      id: `ALT-${item.equipment_id}`,
      equipment_id: item.equipment_id,
      equipment_name: item.name,
      severity: item.alert_level === "critical" ? "CRITICAL" : "WARNING",
      fault_type: item.fault_type,
      rul_hours: item.rul_hours,
      timestamp: item.last_updated,
      acknowledged: false
    }));
}

function offlineEquipment(id: string): EquipmentDetail {
  const item = offlineFleet().find((unit) => unit.equipment_id === id) ?? demoFleet[0];
  const history = Array.from({ length: Math.max(1, item.reading_count || 6) }, (_, index) => ({
    timestamp: new Date(Date.now() - (item.reading_count - index) * 3600000).toISOString(),
    rul: Math.max(1, item.rul_hours + (item.reading_count - index) * 8),
    vibration_rms: 2 + index * 0.4,
    temperature: 38 + index,
    kurtosis: 3 + index * 0.15
  }));
  return {
    ...item,
    history,
    fault_probability: {
      normal_degradation: item.health_score / 100,
      bearing_wear: item.equipment_type === "bearing" ? 0.35 : 0.1,
      overheating: item.alert_level === "healthy" ? 0.05 : 0.2
    },
    maintenance_history: [{ date: "2026-06-14", event: "Browser-local demo record" }]
  };
}

function baseRul(equipmentType: string) {
  return {
    bearing: 500,
    motor: 2000,
    pump: 720,
    gearbox: 400,
    turbine: 350
  }[equipmentType] ?? 300;
}
