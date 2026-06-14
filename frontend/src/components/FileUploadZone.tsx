import { Upload } from "lucide-react";

interface Props {
  file: File | null;
  busy: boolean;
  onFile: (file: File) => void;
}

export default function FileUploadZone({ file, busy, onFile }: Props) {
  return (
    <label className="upload-zone">
      <Upload size={28} />
      <span>{file ? file.name : "Drop CSV or select sensor file"}</span>
      <small>{busy ? "Analysing..." : "CSV columns are previewed before prediction"}</small>
      <input
        type="file"
        accept=".csv,text/csv"
        onChange={(event) => {
          const selected = event.target.files?.[0];
          if (selected) onFile(selected);
        }}
      />
    </label>
  );
}
