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

export async function getFleet() {
  const response = await api.get<FleetUnit[]>("/fleet");
  return response.data;
}

export async function getAlerts() {
  const response = await api.get<AlertItem[]>("/alerts");
  return response.data;
}

export async function acknowledgeAlert(id: string) {
  const response = await api.post<AlertItem>(`/alerts/${id}/acknowledge`);
  return response.data;
}

export async function getEquipment(id: string) {
  const response = await api.get<EquipmentDetail>(`/equipment/${id}`);
  return response.data;
}

export async function createEquipment(payload: EquipmentCreatePayload) {
  const response = await api.post<{ equipment: unknown; status: FleetUnit }>("/equipment", payload);
  return response.data;
}

export async function addSensorReading(equipmentId: string, payload: SensorReadingPayload) {
  const response = await api.post<ReadingStatusResponse>(`/equipment/${equipmentId}/readings`, payload);
  return response.data;
}

export async function getReport() {
  const response = await api.get<ReportRow[]>("/report");
  return response.data;
}

export async function uploadCsv(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post<PredictionResult>("/predict", formData, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return response.data;
}
