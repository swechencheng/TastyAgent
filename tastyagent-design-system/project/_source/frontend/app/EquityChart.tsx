"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Benchmark } from "@/lib/api";

export default function EquityChart({ data }: { data: Benchmark }) {
  // Merge the two curves by date into a single series for the chart.
  const byDate: Record<string, { date: string; strategy?: number; sp500?: number }> = {};
  for (const p of data.strategy_curve) {
    byDate[p.date] = { ...(byDate[p.date] || { date: p.date }), strategy: p.value };
  }
  for (const p of data.sp500_curve) {
    byDate[p.date] = { ...(byDate[p.date] || { date: p.date }), sp500: p.value };
  }
  const series = Object.values(byDate).sort((a, b) => a.date.localeCompare(b.date));

  if (series.length === 0) {
    return (
      <div className="empty">
        No equity history yet. Once the agent records equity snapshots, the curve will
        appear here against the S&amp;P 500.
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={series} margin={{ top: 8, right: 16, bottom: 0, left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#243044" />
        <XAxis dataKey="date" stroke="#8b9bb4" fontSize={12} />
        <YAxis
          stroke="#8b9bb4"
          fontSize={12}
          tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
          domain={["auto", "auto"]}
        />
        <Tooltip
          contentStyle={{ background: "#131a26", border: "1px solid #243044" }}
          formatter={(v: number) => `$${v.toLocaleString()}`}
        />
        <Legend />
        <Line type="monotone" dataKey="strategy" name="IBTastyAgent" stroke="#4c9aff" dot={false} strokeWidth={2} />
        <Line type="monotone" dataKey="sp500" name="S&P 500" stroke="#f0a500" dot={false} strokeWidth={2} />
      </LineChart>
    </ResponsiveContainer>
  );
}
