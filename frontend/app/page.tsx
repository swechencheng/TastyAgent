"use client";

import { useState } from "react";
import useSWR, { useSWRConfig } from "swr";
import {
  Activity as ActivityIcon,
  Bot,
  ChevronDown,
  Clock,
  Layers,
  LayoutDashboard,
  ListChecks,
  Loader2,
  OctagonX,
  Play,
  Settings as SettingsIcon,
} from "lucide-react";
import { toast } from "sonner";

import {
  fetcher,
  Pnl,
  runCycle,
  setKillSwitch,
  setMode,
  startScheduler,
  Settings as SettingsT,
  Status,
  stopScheduler,
  Trade,
  fmtMoneySigned,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Toaster } from "@/components/ui/sonner";
import ConfirmDialog, { ConfirmSpec } from "@/components/ConfirmDialog";
import { cn } from "@/lib/utils";

import Overview from "@/components/screens/Overview";
import Positions from "@/components/screens/Positions";
import Watchlist from "@/components/screens/Watchlist";
import PendingTrades from "@/components/screens/PendingTrades";
import Activity from "@/components/screens/Activity";
import Settings from "@/components/screens/Settings";

const POLL = { refreshInterval: 8000 };
const MODE_LABELS: Record<string, string> = {
  sandbox: "Sandbox",
  live_approval: "Live-approval",
  live_auto: "Live-auto",
};
const NAV = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "positions", label: "Positions", icon: Layers },
  { id: "watchlist", label: "Watchlist", icon: ListChecks },
  { id: "pending", label: "Pending Trades", icon: Clock },
  { id: "activity", label: "Activity", icon: ActivityIcon },
  { id: "settings", label: "Settings", icon: SettingsIcon },
];

export default function App() {
  const { mutate } = useSWRConfig();
  const [route, setRoute] = useState("overview");
  const [confirm, setConfirm] = useState<ConfirmSpec | null>(null);
  const [running, setRunning] = useState(false);

  const status = useSWR<Status>("/api/status", fetcher, POLL);
  const pnl = useSWR<Pnl>("/api/pnl", fetcher, POLL);
  const approvals = useSWR<Trade[]>("/api/approvals", fetcher, POLL);
  const settings = useSWR<SettingsT>("/api/settings", fetcher, POLL);

  const s = status.data;
  const total = pnl.data?.total_pnl ?? 0;
  const pendingCount = approvals.data?.length ?? 0;
  const refreshAll = () =>
    ["/api/status", "/api/pnl", "/api/positions", "/api/approvals", "/api/activity", "/api/benchmark"].forEach((k) =>
      mutate(k)
    );

  const changeMode = (m: string) => {
    if (!s || m === s.mode) return;
    if (m.startsWith("live")) {
      setConfirm({
        title: "Switch to a live trading mode?",
        body: `You are switching to ${m === "live_auto" ? "Live-auto (fully autonomous)" : "Live-approval"}. This trades a real account. Type LIVE to confirm.`,
        confirmLabel: "Switch to live",
        danger: true,
        requireType: "LIVE",
        onConfirm: async () => {
          setConfirm(null);
          try {
            await setMode(m);
            toast.success(`Mode set to ${MODE_LABELS[m] ?? m}`);
            refreshAll();
          } catch {
            toast.error("Could not change mode");
          }
        },
      });
    } else {
      setMode(m)
        .then(() => {
          toast.success(`Mode set to ${MODE_LABELS[m] ?? m}`);
          refreshAll();
        })
        .catch(() => toast.error("Could not change mode"));
    }
  };

  const toggleAuto = async () => {
    if (!s) return;
    try {
      if (s.scheduler_running) {
        await stopScheduler();
        toast.success("Scheduler stopped");
      } else {
        const iv = settings.data?.scheduler.interval_seconds ?? 300;
        const mh = settings.data?.scheduler.market_hours_only ?? true;
        await startScheduler(iv, mh);
        toast.success("Scheduler started");
      }
      mutate("/api/status");
    } catch {
      toast.error("Could not toggle the scheduler");
    }
  };

  const askKill = () => {
    if (!s) return;
    setConfirm({
      title: s.kill_switch ? "Disengage kill switch?" : "Engage kill switch?",
      body: s.kill_switch
        ? "The agent will resume opening new positions on the next cycle."
        : "Halts ALL new entries instantly. Open positions are unaffected. You can disengage at any time.",
      confirmLabel: s.kill_switch ? "Disengage" : "Engage kill switch",
      danger: !s.kill_switch,
      onConfirm: async () => {
        const was = s.kill_switch;
        setConfirm(null);
        try {
          await setKillSwitch(!was);
          toast[was ? "success" : "error"](was ? "Kill switch disengaged" : "Kill switch ENGAGED — all new entries halted");
          mutate("/api/status");
        } catch {
          toast.error("Could not toggle the kill switch");
        }
      },
    });
  };

  const onRun = async () => {
    setRunning(true);
    try {
      await runCycle();
      toast.success("Cycle complete");
      refreshAll();
    } catch {
      toast.error("Cycle failed");
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col">
      {/* ---- Status bar ---- */}
      <header className="flex h-14 flex-shrink-0 items-center gap-4 border-b border-border bg-black px-5">
        <div className="text-[18px] font-bold tracking-[-0.02em]">
          Tasty<span className="text-brand">Agent</span>
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-surface-2 px-3 py-1.5 text-[13px] hover:border-border-strong">
              <Bot className="size-[15px]" />
              {s ? MODE_LABELS[s.mode] ?? s.mode : "—"}
              <ChevronDown className="size-3.5" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start">
            {Object.entries(MODE_LABELS).map(([v, l]) => (
              <DropdownMenuItem key={v} active={s?.mode === v} onSelect={() => changeMode(v)}>
                {l}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        {s && (
          <Badge variant={s.market_open ? "open" : "warn"} dot={s.market_open}>
            Market {s.market_open ? "Open" : "Closed"}
          </Badge>
        )}

        <button
          onClick={toggleAuto}
          className={cn(
            "inline-flex items-center gap-2 rounded-lg border px-4 py-1.5 text-sm font-semibold transition-colors",
            s?.scheduler_running
              ? "border-gain/50 bg-gain-soft text-gain"
              : "border-border bg-transparent text-muted-foreground hover:border-border-strong"
          )}
        >
          <span className={cn("size-2 rounded-full", s?.scheduler_running ? "bg-gain" : "bg-text-faint")} />
          Auto: {s?.scheduler_running ? "ON" : "OFF"}
        </button>

        <div className="ml-auto flex items-baseline gap-2">
          <span className="text-[11px] uppercase tracking-[0.06em] text-muted-foreground">P/L</span>
          <span className={cn("font-mono text-base font-semibold tabular-nums", total > 0 ? "text-gain" : total < 0 ? "text-loss" : "")}>
            {fmtMoneySigned(total)}
          </span>
        </div>

        {s?.scheduler_running && (
          <div className="hidden items-center gap-2 text-[11px] text-text-faint md:inline-flex">
            <span className="live-dot size-2 rounded-full bg-gain" />
            live
          </div>
        )}

        <button
          onClick={askKill}
          className={cn(
            "inline-flex items-center gap-2 rounded-lg border border-brand px-4 py-1.5 text-sm font-semibold transition-colors",
            s?.kill_switch ? "bg-brand text-white" : "bg-transparent text-brand hover:bg-brand-soft"
          )}
        >
          <OctagonX className="size-4" />
          {s?.kill_switch ? "Kill switch ON" : "Kill switch"}
        </button>
      </header>

      <div className="flex min-h-0 flex-1">
        {/* ---- Sidebar ---- */}
        <nav className="flex w-[220px] flex-shrink-0 flex-col gap-2 border-r border-border bg-black p-3 max-[680px]:fixed max-[680px]:inset-x-0 max-[680px]:bottom-0 max-[680px]:z-50 max-[680px]:w-full max-[680px]:flex-row max-[680px]:border-r-0 max-[680px]:border-t">
          <div className="flex flex-1 flex-col gap-0.5 max-[680px]:flex-row">
            {NAV.map((nv) => {
              const active = route === nv.id;
              return (
                <button
                  key={nv.id}
                  onClick={() => setRoute(nv.id)}
                  className={cn(
                    "relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors [&_svg]:size-5",
                    active ? "bg-brand-soft text-white [&_svg]:text-brand" : "text-muted-foreground hover:bg-surface hover:text-foreground"
                  )}
                >
                  <nv.icon />
                  <span className="max-[680px]:hidden">{nv.label}</span>
                  {nv.id === "pending" && pendingCount > 0 && (
                    <span className="ml-auto inline-flex h-[18px] min-w-[18px] items-center justify-center rounded-full bg-brand px-1 text-[10px] font-bold leading-none text-white max-[680px]:absolute max-[680px]:right-1 max-[680px]:top-1 max-[680px]:ml-0">
                      {pendingCount}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
          <Button onClick={onRun} disabled={running} className="w-full max-[680px]:hidden">
            {running ? <Loader2 className="size-[18px] animate-spin" /> : <Play className="size-[18px]" />}
            {running ? "Running cycle…" : "Run cycle"}
          </Button>
        </nav>

        {/* ---- Content ---- */}
        <main className="flex-1 overflow-y-auto px-8 pb-16 pt-7 max-[680px]:px-4 max-[680px]:pb-24">
          {status.error ? (
            <div className="mx-auto mt-20 max-w-md rounded-xl border border-loss/40 bg-loss-soft p-6 text-center text-sm text-loss">
              Could not reach the API at <code>:8000</code>. Start the backend, then this dashboard will populate.
            </div>
          ) : (
            <>
              {s?.kill_switch && (
                <div className="mb-5 flex items-center gap-2.5 rounded-[10px] border border-brand/50 bg-brand-soft px-4 py-3 text-[13px] font-medium text-brand">
                  <OctagonX className="size-4" />
                  Kill switch engaged — the agent will not open new positions.
                </div>
              )}
              {route === "overview" && <Overview goTo={setRoute} />}
              {route === "positions" && <Positions />}
              {route === "watchlist" && <Watchlist />}
              {route === "pending" && <PendingTrades />}
              {route === "activity" && <Activity />}
              {route === "settings" && <Settings mode={s?.mode ?? "sandbox"} onModeChange={changeMode} />}
            </>
          )}
        </main>
      </div>

      <ConfirmDialog spec={confirm} onClose={() => setConfirm(null)} />
      <Toaster />
    </div>
  );
}
