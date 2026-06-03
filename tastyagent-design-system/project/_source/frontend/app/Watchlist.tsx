"use client";

import { useState } from "react";
import useSWR, { useSWRConfig } from "swr";
import {
  addToWatchlist,
  API_BASE,
  fetcher,
  fmtPct,
  importWatchlist,
  RankedSymbol,
  removeFromWatchlist,
  TastytradeWatchlist,
  toggleWatchlist,
  WatchlistItem,
} from "@/lib/api";

export default function Watchlist() {
  const { mutate } = useSWRConfig();
  const list = useSWR<WatchlistItem[]>("/api/watchlist", fetcher);
  const ranked = useSWR<RankedSymbol[]>("/api/watchlist/ranked", fetcher, {
    revalidateOnFocus: false,
    shouldRetryOnError: false,
  });
  const [newSym, setNewSym] = useState("");
  const [ttLists, setTtLists] = useState<TastytradeWatchlist[] | null>(null);
  const [loadingTt, setLoadingTt] = useState(false);

  const ivr: Record<string, RankedSymbol> = {};
  (ranked.data || []).forEach((r) => (ivr[r.symbol] = r));

  const refresh = () => {
    mutate("/api/watchlist");
    mutate("/api/watchlist/ranked");
  };

  const add = async () => {
    const s = newSym.trim().toUpperCase();
    if (!s) return;
    await addToWatchlist(s);
    setNewSym("");
    refresh();
  };

  const loadTt = async () => {
    setLoadingTt(true);
    try {
      const r = await fetch(`${API_BASE}/api/tastytrade-watchlists`);
      setTtLists(r.ok ? await r.json() : []);
    } finally {
      setLoadingTt(false);
    }
  };

  // Sort by IV rank (highest first) — where the agent will focus.
  const rows = (list.data || [])
    .slice()
    .sort((a, b) => (ivr[b.symbol]?.iv_rank ?? -1) - (ivr[a.symbol]?.iv_rank ?? -1));

  return (
    <section className="panel">
      <h2>
        Watchlist — the agent&apos;s universe
        {ranked.error && <span className="tag" style={{ marginLeft: 8 }}>IV rank needs the prod grant</span>}
      </h2>

      <div style={{ display: "flex", gap: 8, marginBottom: 12, flexWrap: "wrap" }}>
        <input
          value={newSym}
          onChange={(e) => setNewSym(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && add()}
          placeholder="Add ticker (e.g. NFLX)"
          style={{ flex: "0 0 200px" }}
        />
        <button onClick={add}>Add</button>
        <button onClick={loadTt} disabled={loadingTt}>
          {loadingTt ? "Loading…" : "Browse tastytrade lists"}
        </button>
      </div>

      <table>
        <thead>
          <tr>
            <th>Symbol</th>
            <th className="num">IV rank</th>
            <th className="num">Liq</th>
            <th>Source</th>
            <th>On</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {rows.map((w) => (
            <tr key={w.symbol} style={{ opacity: w.enabled ? 1 : 0.5 }}>
              <td>{w.symbol}</td>
              <td className="num">{ivr[w.symbol]?.iv_rank != null ? fmtPct(ivr[w.symbol].iv_rank) : "—"}</td>
              <td className="num">{ivr[w.symbol]?.liquidity_rating ?? "—"}</td>
              <td className="rationale">{w.source}</td>
              <td>
                <input
                  type="checkbox"
                  checked={w.enabled}
                  onChange={async (e) => {
                    await toggleWatchlist(w.symbol, e.target.checked);
                    refresh();
                  }}
                />
              </td>
              <td>
                <button
                  className="reject"
                  onClick={async () => {
                    await removeFromWatchlist(w.symbol);
                    refresh();
                  }}
                >
                  Remove
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {ttLists && (
        <div style={{ marginTop: 18 }}>
          <h2>tastytrade recommended lists</h2>
          {ttLists.length === 0 ? (
            <div className="empty">Couldn&apos;t load — needs the production read-only grant.</div>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>List</th>
                  <th className="num">Symbols</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {ttLists.map((w) => (
                  <tr key={w.name}>
                    <td>{w.name}</td>
                    <td className="num">{w.symbols.length}</td>
                    <td>
                      <button
                        className="approve"
                        onClick={async () => {
                          await importWatchlist(w.symbols, `tt:${w.name}`);
                          refresh();
                        }}
                      >
                        Import all
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </section>
  );
}
