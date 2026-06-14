import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid } from "recharts";

interface SensorChartProps<T> {
  data: T[];
  dataKey: keyof T & string;
  xKey?: keyof T & string;
  height?: number;
}

export default function SensorChart<T extends object>({
  data,
  dataKey,
  xKey = "timestamp" as keyof T & string,
  height = 280
}: SensorChartProps<T>) {
  return (
    <div className="chart-wrap" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
          <XAxis dataKey={xKey} tick={{ fill: "#94a3b8", fontSize: 11 }} minTickGap={28} />
          <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
          <Tooltip contentStyle={{ background: "#020617", border: "1px solid #1e293b", color: "#e2e8f0" }} />
          <Line type="monotone" dataKey={dataKey} stroke="#00D4FF" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
