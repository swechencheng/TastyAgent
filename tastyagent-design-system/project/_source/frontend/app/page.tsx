"use client";

import { useState } from "react";
import useSWR, { useSWRConfig } from "swr";
import EquityChart from "./EquityChart";
import Watchlist from "./Watchlist";
import {
  approveTrade,
  Benchmark,
  fetcher,
  fmtMoney,
  fmtPct,
  Pnl,
  rejectTrade,
  runCycle,
  setKillSwitch,
  setMode,
  startScheduler,
  Status,
  stopScheduler,
  Trade,
} from "@/lib/api";

const MODES = ["sandbox", "live_approval", "live_auto", "backtest"];
const POLL = { refreshInterval: 8000 };

function signClass(n: number) {
  return n > 0 ? "pos" : n < 0 ? "neg" : "";
}

export default function Dashboard() {
  const { mutate } = useSWRConfig();
  const [busy, setBusy] = useState(false);
  const status = useSWR<Status>("/api/status", fetcher, POLL);
  const pnl = useSWR<Pnl>("/api/pnl", fetcher, POLL);
  const positions = useSWR<Trade[]>("/api/positions", fetcher, POLL);
  const closed = useSWR<Trade[]>("/api/trades/closed", fetcher, POLL);
  const approvals = useSWR<Trade[]>("/api/approvals", fetcher, POLL);
  const benchmark = useSWR<Benchmark>("/api/benchmark", fetcher, POLL);

  const refreshAll = () =>
    ["/api/status", "/api/pnl", "/api/positions", "/api/trades/closed", "/api/approvals", "/api/benchmark"].forEach(
      (k) => mutate(k)
    );

  const s = status.data;
  const p = pnl.data;
  const wins = (closed.data || []).filter((t) => t.is_win === true);
  const losses = (closed.data || []).filter((t) => t.is_win === false);

  return (
    <div className="container">
      <header className="topbar">
        <div className="brand">
          Tasty<span>Agent</span>
        </div>
        <div className="controls">
          {s && (
            <>
              <span className={`pill ${s.market_open ? "open" : "closed"}`}>
                Market {s.market_open ? "Open" : "Closed"}
              </span>
              <span className="pill">Capital {fmtMoney(s.starting_capital)}</span>
              <select
                value={s.mode}
                onChange={async (e) => {
                  await setMode(e.target.value);
                  refreshAll();
                }}
              >
                {MODES.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
              <button
                disabled={busy}
                onClick={async () => {
                  setBusy(true);
                  try {
                    await runCycle();
                  } catch (e) {
                    alert(`Cycle failed: ${e}`);
                  } finally {
                    setBusy(false);
                    refreshAll();
                  }
                }}
              >
                {busy ? "Running cycle…" : "Run cycle"}
              </button>
              <button
                className={`auto ${s.scheduler_running ? "engaged" : ""}`}
                onClick={async () => {
                  s.scheduler_running ? await stopScheduler() : await startScheduler();
                  refreshAll();
                }}
              >
                {s.scheduler_running ? "Auto: ON" : "Auto: OFF"}
              </button>
              <button
                className={`kill ${s.kill_switch ? "engaged" : ""}`}
                onClick={async () => {
                  await setKillSwitch(!s.kill_switch);
                  refreshAll();
                }}
              >
                {s.kill_switch ? "Kill switch ON" : "Kill switch"}
              </button>
            </>
          )}
        </div>
      </header>

      {/* P/L cards */}
      {p && (
        <div className="grid cards">
          <div className="card">
            <div className="label">Total P/L</div>
            <div className={`value ${signClass(p.total_pnl)}`}>{fmtMoney(p.total_pnl)}</div>
          </div>
          <div className="card">
            <div className="label">Profit %</div>
            <div className={`value ${signClass(p.profit_pct || 0)}`}>{fmtPct(p.profit_pct)}</div>
          </div>
          <div className="card">
            <div className="label">Realized</div>
            <div className={`value ${signClass(p.realized_pnl)}`}>{fmtMoney(p.realized_pnl)}</div>
          </div>
          <div className="card">
            <div className="label">Unrealized</div>
            <div className={`value ${signClass(p.unrealized_pnl)}`}>{fmtMoney(p.unrealized_pnl)}</div>
          </div>
          <div className="card">
            <div className="label">Win rate</div>
            <div className="value">
              {fmtPct(p.win_rate)} <span className="tag">{p.wins}W / {p.losses}L</span>
            </div>
          </div>
          <div className="card">
            <div className="label">Open / Closed</div>
            <div className="value">
              {p.open_count} / {p.closed_count}
            </div>
          </div>
        </div>
      )}

      {/* Equity vs S&P */}
      <section className="panel">
        <h2>
          Equity curve vs. S&amp;P 500
          {benchmark.data && (
            <span className="tag" style={{ marginLeft: 10 }}>
              outperf {fmtPct(benchmark.data.outperformance_pct)}
            </span>
          )}
        </h2>
        {benchmark.data && <EquityChart data={benchmark.data} />}
      </section>

      {/* Approvals (live_approval mode) */}
      {(approvals.data?.length ?? 0) > 0 && (
        <section className="panel">
          <h2>Pending approval</h2>
          <table>
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Strategy</th>
                <th className="num">Contracts</th>
                <th className="num">Credit</th>
                <th className="num">PoP</th>
                <th>Rationale</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {approvals.data!.map((t) => (
                <tr key={t.id}>
                  <td>{t.symbol}</td>
                  <td>{t.strategy}</td>
                  <td className="num">{t.contracts}</td>
                  <td className="num">{fmtMoney(t.entry_credit)}</td>
                  <td className="num">{fmtPct(t.probability_of_profit)}</td>
                  <td className="rationale">{t.rationale}</td>
                  <td>
                    <button
                      className="approve"
                      onClick={async () => {
                        await approveTrade(t.id);
                        refreshAll();
                      }}
                    >
                      Approve
                    </button>{" "}
                    <button
                      className="reject"
                      onClick={async () => {
                        await rejectTrade(t.id);
                        refreshAll();
                      }}
                    >
                      Reject
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {/* Watchlist / universe */}
      <Watchlist />

      {/* Open positions */}
      <section className="panel">
        <h2>Open positions</h2>
        {positions.data && positions.data.length > 0 ? (
          <table>
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Strategy</th>
                <th className="num">Qty</th>
                <th className="num">Credit</th>
                <th className="num">PoP</th>
                <th className="num">Unrealized</th>
                <th className="num">DTE</th>
                <th>Why</th>
              </tr>
            </thead>
            <tbody>
              {positions.data.map((t) => (
                <tr key={t.id}>
                  <td>{t.symbol}</td>
                  <td>{t.strategy}</td>
                  <td className="num">{t.contracts}</td>
                  <td className="num">{fmtMoney(t.entry_credit)}</td>
                  <td className="num">{fmtPct(t.probability_of_profit)}</td>
                  <td className={`num ${signClass(t.unrealized_pnl)}`}>{fmtMoney(t.unrealized_pnl)}</td>
                  <td className="num">{t.dte_at_entry}</td>
                  <td className="rationale">{t.rationale}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="empty">No open positions.</div>
        )}
      </section>

      {/* Win / loss */}
      <div className="two-col">
        <section className="panel">
          <h2>Winning trades</h2>
          <TradeList trades={wins} />
        </section>
        <section className="panel">
          <h2>Losing trades</h2>
          <TradeList trades={losses} />
        </section>
      </div>
    </div>
  );
}

function TradeList({ trades }: { trades: Trade[] }) {
  if (trades.length === 0) return <div className="empty">None yet.</div>;
  return (
    <table>
      <thead>
        <tr>
          <th>Symbol</th>
          <th>Strategy</th>
          <th className="num">PoP</th>
          <th className="num">P/L</th>
          <th>Exit</th>
        </tr>
      </thead>
      <tbody>
        {trades.map((t) => (
          <tr key={t.id}>
            <td>{t.symbol}</td>
            <td>{t.strategy}</td>
            <td className="num">{fmtPct(t.probability_of_profit)}</td>
            <td className={`num ${t.is_win ? "pos" : "neg"}`}>{fmtMoney(t.realized_pnl)}</td>
            <td className="rationale">{t.exit_reason || "—"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
