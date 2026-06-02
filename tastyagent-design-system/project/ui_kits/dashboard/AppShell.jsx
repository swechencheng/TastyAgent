/* AppShell — status bar + sidebar + routed content (v3: toast queue + live feed) */

/* ---- Live trade event feed ------------------------------------------------- */
const LIVE_EVENTS = [
  { msg:"NVDA short strangle filled — $312 credit received", tone:"filled" },
  { msg:"AMD put credit spread filled — $156 credit received", tone:"filled" },
  { msg:"SPY put spread filled — $88 credit received", tone:"filled" },
  { msg:"AAPL put spread closed — +$96 realized (+52% of max)", tone:"profit" },
  { msg:"MSFT naked put closed — +$110 realized (+52% of max)", tone:"profit" },
  { msg:"GOOGL strangle closed — +$142.50 realized (ahead of pace)", tone:"profit" },
  { msg:"QQQ iron condor closed — +$88 realized (+54% of max)", tone:"profit" },
  { msg:"NFLX iron condor closed — −$88 realized (21 DTE exit)", tone:"loss" },
  { msg:"AMZN call spread closed — −$76 realized (21 DTE exit)", tone:"loss" },
  { msg:"META naked put rolled out — 30 days added, +$18 credit", tone:"managed" },
  { msg:"TSLA iron condor defended — untested side rolled, +$12 credit", tone:"managed" },
  { msg:"NVDA strangle rolled out — 21 DTE reached, 30 days added", tone:"managed" },
];

function StatusBar({ status, pnl, onMode, onAuto, onRun, onKill, running, setConfirm }) {
  useLucide();
  const MODES = { sandbox:"Sandbox", live_approval:"Live-approval", live_auto:"Live-auto" };
  const [modeOpen, setModeOpen] = useState(false);
  return (
    <header className="ta-statusbar">
      <div className="ta-wordmark">Tasty<span>Agent</span></div>

      <div className="ta-mode-select">
        <button className="ta-mode-btn" onClick={() => setModeOpen(!modeOpen)}>
          <Icon name="bot" size={15} />{MODES[status.mode]}<Icon name="chevron-down" size={14} />
        </button>
        {modeOpen && (
          <div className="ta-menu">
            {Object.entries(MODES).map(([v, l]) => (
              <button key={v} className={v === status.mode ? "active" : ""}
                onClick={() => { setModeOpen(false); onMode(v); }}>{l}</button>
            ))}
          </div>
        )}
      </div>

      <Pill tone={status.market_open ? "open" : "warn"} dot={status.market_open}>
        Market {status.market_open ? "Open" : "Closed"}
      </Pill>

      <button className={`ta-btn ta-btn-auto ${status.scheduler_running ? "on" : ""}`} onClick={onAuto}>
        <span className="ta-auto-dot" />Auto: {status.scheduler_running ? "ON" : "OFF"}
      </button>

      <div className="ta-statusbar-pl">
        <span className="ta-pl-label">P/L</span>
        <span className={`ta-pl-value ${signClass(pnl.total_pnl)}`}>{fmtMoney(pnl.total_pnl)}</span>
      </div>

      <div className="ta-live"><span className="ta-live-dot" />live · updated 3s ago</div>

      <button className={`ta-btn ta-kill ${status.kill_switch ? "on" : ""}`}
        onClick={() => setConfirm({
          title: status.kill_switch ? "Disengage kill switch?" : "Engage kill switch?",
          body: status.kill_switch ? "The agent will resume opening new positions on the next cycle." : "Halts ALL new entries instantly. Open positions are unaffected. You can disengage at any time.",
          confirmLabel: status.kill_switch ? "Disengage" : "Engage kill switch",
          danger: !status.kill_switch, onConfirm: onKill,
        })}>
        <Icon name="octagon-x" size={16} />{status.kill_switch ? "Kill switch ON" : "Kill switch"}
      </button>
    </header>
  );
}

function Sidebar({ route, goTo, onRun, running, pendingCount }) {
  useLucide();
  const NAV = [
    { id:"overview",  label:"Overview",       icon:"layout-dashboard" },
    { id:"positions", label:"Positions",      icon:"layers" },
    { id:"watchlist", label:"Watchlist",      icon:"list-checks" },
    { id:"pending",   label:"Pending Trades", icon:"clock", badge: pendingCount },
    { id:"activity",  label:"Activity",       icon:"activity" },
    { id:"settings",  label:"Settings",       icon:"settings" },
  ];
  return (
    <nav className="ta-sidebar">
      <div className="ta-nav">
        {NAV.map((n) => (
          <button key={n.id} className={`ta-nav-item ${route === n.id ? "active" : ""}`} onClick={() => goTo(n.id)}>
            <Icon name={n.icon} size={20} />
            <span>{n.label}</span>
            {n.badge > 0 && <span className="ta-nav-badge">{n.badge}</span>}
          </button>
        ))}
      </div>
      <button className="ta-btn ta-btn-primary ta-run" onClick={onRun} disabled={running}>
        <Icon name={running ? "loader" : "play"} size={18} className={running ? "spin" : ""} />
        <span>{running ? "Running cycle…" : "Run cycle"}</span>
      </button>
    </nav>
  );
}

function App() {
  useLucide();
  const [route, setRoute]       = useState("overview");
  const [data, setData]         = useState(MOCK);
  const [status, setStatus]     = useState(MOCK.status);
  const [running, setRunning]   = useState(false);
  const [confirm, setConfirm]   = useState(null);
  const [approvedCount, setApprovedCount] = useState(0);
  const [rejectedCount, setRejectedCount] = useState(0);
  const { toasts, push: pushToast } = useToasts();

  /* ---- Live feed: fire a random trade event every 9–18s when scheduler on -- */
  const feedIdx = useRef(0);
  useEffect(() => {
    if (!status.scheduler_running || status.kill_switch) return;
    const fire = () => {
      const ev = LIVE_EVENTS[feedIdx.current % LIVE_EVENTS.length];
      feedIdx.current++;
      pushToast(ev.msg, ev.tone, 5000);
    };
    // Fire first event after a short delay so the UI settles
    const first = setTimeout(fire, 3500);
    const interval = setInterval(fire, 12000);
    return () => { clearTimeout(first); clearInterval(interval); };
  }, [status.scheduler_running, status.kill_switch]);

  const goTo = (r) => setRoute(r);

  const runCycle = () => {
    setRunning(true);
    setTimeout(() => {
      setRunning(false);
      pushToast("Cycle complete — 2 opened, 1 managed");
      setTimeout(() => pushToast("NVDA short strangle filled — $312 credit received", "filled"), 900);
      setTimeout(() => pushToast("AMD put credit spread filled — $156 credit received", "filled"), 1800);
    }, 2200);
  };

  const toggleAuto = () => {
    const nowOn = !status.scheduler_running;
    setStatus((s) => ({ ...s, scheduler_running: nowOn }));
    pushToast(nowOn ? "Scheduler started" : "Scheduler stopped");
  };

  const toggleKill = () => {
    const wasOn = status.kill_switch;
    setStatus((s) => ({ ...s, kill_switch: !s.kill_switch }));
    setConfirm(null);
    pushToast(wasOn ? "Kill switch disengaged" : "Kill switch ENGAGED — all new entries halted", wasOn ? "ok" : "error");
  };

  const setMode = (m) => {
    if (m === status.mode) return;
    if (m.startsWith("live")) {
      setConfirm({
        title: "Switch to a live trading mode?", requireType: "LIVE",
        body: `You are switching to ${m === "live_auto" ? "Live-auto (fully autonomous)" : "Live-approval"}. This trades a real account. Type LIVE to confirm.`,
        confirmLabel: "Switch to live", danger: true,
        onConfirm: () => {
          setStatus((s) => ({ ...s, mode: m, requires_approval: m === "live_approval" }));
          setData((d) => ({ ...d, approvals: m === "live_approval" ? MOCK.approvals : [] }));
          setConfirm(null);
          pushToast(`Mode set to ${m}`);
        },
      });
    } else {
      setStatus((s) => ({ ...s, mode: m, requires_approval: false }));
      setData((d) => ({ ...d, approvals: [] }));
      pushToast(`Mode set to ${m}`);
    }
  };

  const approve = (t) => {
    setData((d) => ({ ...d, approvals: d.approvals.filter((a) => a.id !== t.id) }));
    setApprovedCount((n) => n + 1);
    pushToast(`${t.symbol} ${t.strategy} approved — sending to broker`, "ok");
    setTimeout(() => pushToast(`${t.symbol} order filled — $${t.entry_credit} credit received`, "filled"), 1800);
  };

  const reject = (t) => {
    setData((d) => ({ ...d, approvals: d.approvals.filter((a) => a.id !== t.id) }));
    setRejectedCount((n) => n + 1);
    pushToast(`${t.symbol} rejected`, "error");
  };

  const liveData = { ...data, status, pnl: data.pnl };
  const pendingCount = data.approvals.length;

  return (
    <div className="ta-app">
      <StatusBar status={status} pnl={data.pnl} onMode={setMode} onAuto={toggleAuto} onRun={runCycle} onKill={toggleKill} running={running} setConfirm={setConfirm} />
      <div className="ta-body">
        <Sidebar route={route} goTo={goTo} onRun={runCycle} running={running} pendingCount={pendingCount} />
        <main className={`ta-content ${status.kill_switch ? "ta-killed" : ""}`}>
          {status.kill_switch && (
            <div className="ta-kill-banner">
              <Icon name="octagon-x" size={16} />Kill switch engaged — the agent will not open new positions.
            </div>
          )}
          {route === "overview"  && <Overview data={liveData} onApprove={approve} onReject={reject} goTo={goTo} />}
          {route === "positions" && <Positions data={liveData} />}
          {route === "watchlist" && <WatchlistScreen data={liveData} toast={pushToast} />}
          {route === "pending"   && <PendingTrades data={liveData} onApprove={approve} onReject={reject} approvedCount={approvedCount} rejectedCount={rejectedCount} />}
          {route === "activity"  && <Activity data={liveData} />}
          {route === "settings"  && <Settings data={liveData} toast={pushToast} onModeChange={setMode} />}
        </main>
      </div>
      <ConfirmDialog open={!!confirm} {...(confirm || {})} onCancel={() => setConfirm(null)} />
      <ToastStack toasts={toasts} />
    </div>
  );
}
window.App = App;
