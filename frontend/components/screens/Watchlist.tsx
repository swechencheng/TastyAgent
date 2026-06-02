"use client";

import { useState } from "react";
import useSWR, { useSWRConfig } from "swr";
import { Plus, ListPlus, Trash2 } from "lucide-react";
import { toast } from "sonner";

import {
  addToWatchlist,
  fetcher,
  importWatchlist,
  RankedSymbol,
  removeFromWatchlist,
  TastytradeWatchlist,
  toggleWatchlist,
  WatchlistItem,
} from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Empty, ErrorNote, IvrHeat, Loading, PageHeader, Pagination, num, usePagination } from "@/components/common";
import { cn } from "@/lib/utils";

const POLL = { refreshInterval: 15000 };
const toPct = (v: number | null | undefined) => (v == null ? null : v <= 1.5 ? v * 100 : v);

export default function Watchlist() {
  const { mutate } = useSWRConfig();
  const [newSym, setNewSym] = useState("");
  const [showImport, setShowImport] = useState(false);

  const wl = useSWR<WatchlistItem[]>("/api/watchlist", fetcher, POLL);
  const ranked = useSWR<RankedSymbol[]>("/api/watchlist/ranked", fetcher, POLL);
  const ttLists = useSWR<TastytradeWatchlist[]>(showImport ? "/api/tastytrade-watchlists" : null, fetcher);

  const refresh = () => { mutate("/api/watchlist"); mutate("/api/watchlist/ranked"); };

  // Derive rows + pagination BEFORE any conditional return so hook order is stable.
  const rankBy: Record<string, RankedSymbol> = {};
  (ranked.data || []).forEach((r) => (rankBy[r.symbol] = r));

  const rows = (wl.data || []).map((w) => {
    const r = rankBy[w.symbol];
    return {
      symbol: w.symbol,
      enabled: w.enabled,
      source: w.source,
      iv_rank: toPct(r?.iv_rank),
      iv_pctile: toPct(r?.iv_percentile),
      liquidity: r?.liquidity_rating ?? null,
    };
  });
  rows.sort((a, b) => (b.iv_rank ?? -1) - (a.iv_rank ?? -1));
  const pg = usePagination(rows, 10);

  if (wl.error) return <ErrorNote msg="Could not load the watchlist." />;
  if (!wl.data) return <Loading />;

  const add = async () => {
    const s = newSym.trim().toUpperCase();
    if (!s || rows.some((r) => r.symbol === s)) return;
    setNewSym("");
    try { await addToWatchlist(s); toast.success(`Added ${s} to the watchlist`); refresh(); }
    catch { toast.error(`Could not add ${s}`); }
  };
  const remove = async (s: string) => {
    try { await removeFromWatchlist(s); toast.success(`Removed ${s}`); refresh(); }
    catch { toast.error(`Could not remove ${s}`); }
  };
  const toggle = async (s: string, enabled: boolean) => {
    try { await toggleWatchlist(s, enabled); refresh(); }
    catch { toast.error(`Could not update ${s}`); }
  };
  const importList = async (l: TastytradeWatchlist) => {
    try { await importWatchlist(l.symbols, `tt:${l.name}`); toast.success(`Imported ${l.symbols.length} symbols from ${l.name}`); refresh(); }
    catch { toast.error(`Could not import ${l.name}`); }
  };

  return (
    <div className="max-w-[1080px]">
      <PageHeader title="Watchlist">
        {rows.length} symbols · seeded from tastytrade <b className="font-semibold text-foreground">High Options Volume</b>. The agent does the expensive chain work on the highest-IVR liquid names each cycle.
      </PageHeader>

      <div className="mb-[18px] flex flex-wrap items-center gap-2.5">
        <Input
          placeholder="Add ticker (e.g. NFLX)"
          value={newSym}
          onChange={(e) => setNewSym(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && add()}
          className="w-[200px]"
        />
        <Button onClick={add}><Plus className="size-4" /> Add</Button>
        <Button variant="secondary" onClick={() => setShowImport(!showImport)}>
          <ListPlus className="size-4" /> Browse tastytrade lists
        </Button>
      </div>

      <Card className="mb-[18px]">
        <CardContent className="p-[18px]">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Symbol</TableHead>
                <TableHead>IV rank</TableHead>
                <TableHead className="text-right">IV %ile</TableHead>
                <TableHead>Liq</TableHead>
                <TableHead>Source</TableHead>
                <TableHead>Enabled</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              {pg.pageItems.map((w) => (
                <TableRow key={w.symbol} className={cn(!w.enabled && "opacity-45")}>
                  <TableCell className="font-semibold">{w.symbol}</TableCell>
                  <TableCell><IvrHeat ivr={w.iv_rank} /></TableCell>
                  <TableCell className={cn("text-right", num)}>{w.iv_pctile == null ? "—" : `${Math.round(w.iv_pctile)}%`}</TableCell>
                  <TableCell>{w.liquidity ?? "—"}</TableCell>
                  <TableCell><span className={cn("text-[11px] text-muted-foreground", num)}>{w.source}</span></TableCell>
                  <TableCell><Switch checked={w.enabled} onCheckedChange={(v) => toggle(w.symbol, v)} aria-label={`Enable ${w.symbol}`} /></TableCell>
                  <TableCell>
                    <button className="rounded-md p-1 text-text-faint hover:bg-surface-2 hover:text-loss" aria-label={`Remove ${w.symbol}`} onClick={() => remove(w.symbol)}>
                      <Trash2 className="size-4" />
                    </button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <Pagination page={pg.page} pageCount={pg.pageCount} onPage={pg.setPage} />
        </CardContent>
      </Card>

      {showImport && (
        <Card>
          <CardHeader><CardTitle>tastytrade recommended lists</CardTitle></CardHeader>
          <CardContent>
            {!ttLists.data ? (
              <Loading label="Fetching tastytrade lists…" />
            ) : ttLists.error ? (
              <ErrorNote msg="Could not fetch tastytrade lists (live-only endpoint)." />
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>List</TableHead>
                    <TableHead className="text-right">Symbols</TableHead>
                    <TableHead />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {ttLists.data.map((l) => (
                    <TableRow key={l.name}>
                      <TableCell className="font-medium">{l.name}</TableCell>
                      <TableCell className={cn("text-right", num)}>{l.symbols.length}</TableCell>
                      <TableCell><Button variant="secondary" size="sm" onClick={() => importList(l)}>Import all</Button></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
