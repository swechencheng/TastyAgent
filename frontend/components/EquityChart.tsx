"use client";

import type { Benchmark } from "@/lib/api";
import { cn } from "@/lib/utils";

/** Clean dual-line SVG equity curve — brand-red strategy vs. muted S&P 500. */
export default function EquityChart({ data }: { data: Benchmark }) {
  const strategy = data.strategy_curve || [];
  const sp500 = data.sp500_curve || [];
  const W = 760;
  const H = 240;
  const pad = { t: 12, r: 16, b: 28, l: 52 };

  if (!strategy || strategy.length < 2) {
    return <div className="py-8 text-center text-[13px] text-text-faint">Equity curve builds as the agent trades.</div>;
  }

  const all = [...strategy, ...sp500];
  const min = Math.min(...all.map((d) => d.value));
  const max = Math.max(...all.map((d) => d.value));
  const n = strategy.length;
  const x = (i: number) => pad.l + (i / (n - 1)) * (W - pad.l - pad.r);
  const y = (v: number) => pad.t + (1 - (v - min) / (max - min || 1)) * (H - pad.t - pad.b);
  const line = (arr: { value: number }[]) =>
    arr.map((d, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(d.value).toFixed(1)}`).join(" ");
  const area = `${line(strategy)} L${x(n - 1)},${H - pad.b} L${x(0)},${H - pad.b} Z`;
  const ticks = [min, (min + max) / 2, max];
  const labelStep = Math.max(1, Math.floor(n / 6));
  const outperf = data.outperformance_pct;

  return (
    <div>
      <div className="mb-2 flex items-center gap-[18px] text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-2">
          <i className="inline-block h-[3px] w-3 rounded-sm bg-brand align-middle" /> TastyAgent
        </span>
        <span className="inline-flex items-center gap-2">
          <i className="inline-block h-[3px] w-3 rounded-sm bg-muted-foreground align-middle" /> S&amp;P 500
        </span>
        {outperf != null && (
          <span
            className={cn(
              "ml-auto rounded-full px-2.5 py-0.5 font-mono",
              outperf >= 0 ? "bg-gain-soft text-gain" : "bg-loss-soft text-loss"
            )}
          >
            outperformance {outperf > 0 ? "+" : outperf < 0 ? "−" : ""}
            {Math.abs(outperf).toFixed(2)}%
          </span>
        )}
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" preserveAspectRatio="xMidYMid meet">
        {ticks.map((t, i) => (
          <g key={i}>
            <line x1={pad.l} x2={W - pad.r} y1={y(t)} y2={y(t)} stroke="hsl(var(--border))" strokeDasharray="3 3" />
            <text x={pad.l - 8} y={y(t) + 4} textAnchor="end" className="fill-text-faint font-mono text-[10px]">
              ${(t / 1000).toFixed(1)}k
            </text>
          </g>
        ))}
        {strategy
          .filter((_, i) => i % labelStep === 0)
          .map((d, i) => (
            <text key={i} x={x(i * labelStep)} y={H - 4} textAnchor="middle" className="fill-text-faint font-mono text-[10px]">
              {d.date}
            </text>
          ))}
        <path d={area} fill="hsl(var(--brand) / 0.13)" />
        {sp500.length > 1 && <path d={line(sp500)} fill="none" stroke="hsl(var(--muted-foreground))" strokeWidth="2" />}
        <path d={line(strategy)} fill="none" stroke="hsl(var(--brand))" strokeWidth="2.5" />
      </svg>
    </div>
  );
}
