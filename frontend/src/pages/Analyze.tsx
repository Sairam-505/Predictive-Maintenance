import { useState } from "react";
import Papa from "papaparse";
import { uploadCsv } from "../api/client";
import FileUploadZone from "../components/FileUploadZone";
import AlertBadge from "../components/AlertBadge";
import type { PredictionResult } from "../types";

export default function Analyze() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string[][]>([]);
  const [result, setResult] = useState<PredictionResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(false);

  function selectFile(nextFile: File) {
    setFile(nextFile);
    setResult(null);
    Papa.parse<string[]>(nextFile, {
      preview: 6,
      complete: (parsed) => setPreview(parsed.data.filter((row) => row.length > 1))
    });
  }

  async function submit() {
    if (!file) return;
    setBusy(true);
    setError(false);
    try {
      setResult(await uploadCsv(file));
    } catch {
      setError(true);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="page">
      <header className="page-header">
        <div>
          <p>CSV Inference</p>
          <h1>Upload & Analyse</h1>
        </div>
      </header>
      <div className="analyze-grid">
        <section className="panel">
          <FileUploadZone file={file} busy={busy} onFile={selectFile} />
          {preview.length > 0 && (
            <div className="preview-table">
              <table>
                <tbody>
                  {preview.map((row, index) => <tr key={index}>{row.map((cell, cellIndex) => <td key={cellIndex}>{cell}</td>)}</tr>)}
                </tbody>
              </table>
            </div>
          )}
          <button className="primary full" disabled={!file || busy} onClick={submit}>Run Prediction</button>
          {error && <button className="error-banner" onClick={submit}>Prediction failed. Retry</button>}
        </section>
        <section className="panel">
          <h2>Prediction Result</h2>
          {result ? (
            <div className="result-stack">
              <AlertBadge value={result.alert_level} />
              <div className="rul-value">{Math.round(result.rul_hours)}h</div>
              <p>{result.equipment_type} · {result.fault_type.replaceAll("_", " ")}</p>
              <div className="confidence"><span style={{ width: `${result.confidence_score * 100}%` }} /></div>
              <blockquote>{result.ai_explanation}</blockquote>
              <p>{result.recommendation}</p>
            </div>
          ) : <p className="muted">Awaiting CSV input.</p>}
        </section>
      </div>
    </section>
  );
}
