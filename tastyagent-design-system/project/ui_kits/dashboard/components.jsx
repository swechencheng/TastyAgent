/* ============================================================================
   IBTastyAgent UI Kit — shared primitives, mock data, helpers  (v2)
   ========================================================================== */
const { useState, useEffect, useRef, useMemo } = React;

/* ---- Icon ----------------------------------------------------------------- */
function Icon({ name, size = 20, className = "", style = {} }) {
  return <i data-lucide={name} className={`ta-icon ${className}`} style={{ width: size, height: size, display: "inline-flex", ...style }} />;
}
function useLucide() { useEffect(() => { if (window.lucide) window.lucide.createIcons(); }); }

/* ---- Formatters ----------------------------------------------------------- */
const fmtMoney = (n) => { const sign = n > 0 ? "+" : n < 0 ? "−" : ""; return `${sign}$${Math.abs(n).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`; };
const fmtMoney0 = (n) => `$${Math.abs(n).toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
const fmtPct = (n) => `${n > 0 ? "+" : n < 0 ? "−" : ""}${Math.abs(n).toFixed(2)}%`;
const signClass = (n) => (n > 0 ? "ta-gain" : n < 0 ? "ta-loss" : "");

/* ---- Pagination ----------------------------------------------------------- */
function usePagination(items, pageSize = 8) {
  const [page, setPage] = useState(0);
  useEffect(() => { setPage(0); }, [items.length]);
  const pageCount = Math.max(1, Math.ceil(items.length / pageSize));
  const safe = Math.min(page, pageCount - 1);
  const pageItems = items.slice(safe * pageSize, (safe + 1) * pageSize);
  return { page: safe, setPage, pageItems, pageCount };
}
function Pagination({ page, pageCount, onPage }) {
  if (pageCount <= 1) return null;
  return (
    <div className="ta-pg">
      <button className="ta-pg-btn" onClick={() => onPage(page - 1)} disabled={page === 0}><Icon name="chevron-left" size={16} />Prev</button>
      <span className="ta-pg-info">{page + 1} of {pageCount}</span>
      <button className="ta-pg-btn" onClick={() => onPage(page + 1)} disabled={page === pageCount - 1}>Next<Icon name="chevron-right" size={16} /></button>
    </div>
  );
}

/* ---- Pill ----------------------------------------------------------------- */
function Pill({ children, tone = "neutral", dot = false, className = "", ...rest }) {
  return <span className={`ta-pill ta-pill-${tone} ${className}`} {...rest}>{dot && <span className="ta-pill-dot" />}{children}</span>;
}

/* ---- Toggle --------------------------------------------------------------- */
function Toggle({ on, onChange, ariaLabel }) {
  return (
    <button role="switch" aria-checked={on} aria-label={ariaLabel} className={`ta-switch ${on ? "on" : ""}`} onClick={() => onChange(!on)}>
      <span className="ta-knob" />
    </button>
  );
}

/* ---- Segmented ------------------------------------------------------------ */
function Segmented({ options, value, onChange }) {
  return (
    <div className="ta-seg" role="tablist">
      {options.map((o) => (
        <button key={o.value} role="tab" aria-selected={value === o.value} className={value === o.value ? "active" : ""} onClick={() => onChange(o.value)}>{o.label}</button>
      ))}
    </div>
  );
}

/* ---- Stat / KPI card ------------------------------------------------------ */
function StatCard({ label, value, delta, deltaTone, sub }) {
  const tone = typeof value === "string" && value[0] === "+" ? "ta-gain" : value && value[0] === "−" ? "ta-loss" : "";
  return (
    <div className="ta-stat">
      <div className="ta-stat-label">{label}</div>
      <div className={`ta-stat-value ${tone}`}>{value}</div>
      {delta != null && <span className={`ta-delta ${deltaTone === "up" ? "up" : deltaTone === "down" ? "down" : "flat"}`}>{deltaTone === "up" ? "▲" : deltaTone === "down" ? "▼" : "•"} {delta}</span>}
      {sub && <span className="ta-delta flat">{sub}</span>}
    </div>
  );
}

/* ---- Buying Power card ---------------------------------------------------- */
function BuyingPowerCard({ bp }) {
  const pct = bp.pct_used;
  const barColor = pct > 80 ? "var(--loss)" : pct > 60 ? "var(--warn)" : "var(--gain)";
  return (
    <div className="ta-stat">
      <div className="ta-stat-label">Buying Power</div>
      <div className="ta-stat-value">{fmtMoney0(bp.remaining)}</div>
      <div className="ta-bp-track"><div className="ta-bp-fill" style={{ width: `${pct}%`, background: barColor }} /></div>
      <div className="ta-bp-meta"><span style={{ color: "var(--text-muted)" }}>{pct}% used</span><span style={{ color: "var(--text-faint)" }}>{fmtMoney0(bp.total)} cap</span></div>
    </div>
  );
}

/* ---- Panel ---------------------------------------------------------------- */
function Panel({ title, action, children, className = "" }) {
  return (
    <section className={`ta-panel ${className}`}>
      {(title || action) && <header className="ta-panel-head">{title && <h2 className="ta-panel-title">{title}</h2>}{action}</header>}
      {children}
    </section>
  );
}

/* ---- Equity chart --------------------------------------------------------- */
function EquityChart({ strategy, sp500, outperf }) {
  const W = 760, H = 240, pad = { t: 12, r: 16, b: 28, l: 52 };
  if (!strategy || strategy.length < 2) return <div className="ta-empty">No equity history yet. The curve builds as the agent trades.</div>;
  const all = [...strategy, ...sp500];
  const min = Math.min(...all.map((d) => d.value));
  const max = Math.max(...all.map((d) => d.value));
  const n = strategy.length;
  const x = (i) => pad.l + (i / (n - 1)) * (W - pad.l - pad.r);
  const y = (v) => pad.t + (1 - (v - min) / (max - min || 1)) * (H - pad.t - pad.b);
  const path = (arr) => arr.map((d, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(d.value).toFixed(1)}`).join(" ");
  const area = `${path(strategy)} L${x(n - 1)},${H - pad.b} L${x(0)},${H - pad.b} Z`;
  const ticks = [min, (min + max) / 2, max];
  const labelStep = Math.max(1, Math.floor(n / 6));
  return (
    <div className="ta-chart">
      <div className="ta-chart-legend">
        <span><i className="lg" style={{ background: "var(--brand)" }} />IBTastyAgent</span>
        <span><i className="lg" style={{ background: "var(--text-muted)" }} />S&amp;P 500</span>
        {outperf != null && <span className="ta-outperf">outperformance {fmtPct(outperf)}</span>}
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" preserveAspectRatio="xMidYMid meet">
        {ticks.map((t, i) => <g key={i}><line x1={pad.l} x2={W - pad.r} y1={y(t)} y2={y(t)} stroke="var(--border)" strokeDasharray="3 3" /><text x={pad.l - 8} y={y(t) + 4} textAnchor="end" className="ta-axis">${(t / 1000).toFixed(1)}k</text></g>)}
        {strategy.filter((_, i) => i % labelStep === 0).map((d, i) => <text key={i} x={x(i * labelStep)} y={H - 4} textAnchor="middle" className="ta-axis">{d.date}</text>)}
        <path d={area} fill="var(--brand-soft)" />
        <path d={path(sp500)} fill="none" stroke="var(--text-muted)" strokeWidth="2" />
        <path d={path(strategy)} fill="none" stroke="var(--brand)" strokeWidth="2.5" />
      </svg>
    </div>
  );
}

/* ---- Confirm dialog ------------------------------------------------------- */
function ConfirmDialog({ open, title, body, confirmLabel, danger, requireType, onConfirm, onCancel }) {
  const [typed, setTyped] = useState("");
  useLucide();
  if (!open) return null;
  const ok = !requireType || typed.trim().toUpperCase() === requireType.toUpperCase();
  return (
    <div className="ta-overlay" onClick={onCancel}>
      <div className="ta-dialog" onClick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
        <div className="ta-dialog-icon"><Icon name={danger ? "triangle-alert" : "info"} size={22} /></div>
        <h3>{title}</h3>
        <p>{body}</p>
        {requireType && <input className="ta-input" placeholder={`Type ${requireType} to confirm`} value={typed} onChange={(e) => setTyped(e.target.value)} style={{ width: "100%", marginTop: 8 }} />}
        <div className="ta-dialog-actions">
          <button className="ta-btn ta-btn-secondary" onClick={onCancel}>Cancel</button>
          <button className={`ta-btn ${danger ? "ta-btn-danger" : "ta-btn-primary"}`} disabled={!ok} onClick={onConfirm}>{confirmLabel}</button>
        </div>
      </div>
    </div>
  );
}

/* ---- Toast stack ---------------------------------------------------------- */
const TOAST_ICONS = {
  ok:      "circle-check",
  error:   "circle-x",
  filled:  "arrow-down-to-line",
  profit:  "trending-up",
  loss:    "trending-down",
  managed: "refresh-cw",
};
const TOAST_LABELS = {
  ok:      "Done",
  error:   "Error",
  filled:  "Order filled",
  profit:  "Closed for profit",
  loss:    "Closed for loss",
  managed: "Trade managed",
};
function ToastStack({ toasts }) {
  useLucide();
  if (!toasts || toasts.length === 0) return null;
  return (
    <div className="ta-toasts">
      {toasts.map((t) => (
        <div key={t.id} className={`ta-toast ta-toast-${t.tone || "ok"}`}>
          <Icon name={TOAST_ICONS[t.tone] || "circle-check"} size={18} style={{ flexShrink: 0, marginTop: 1 }} />
          <div className="ta-toast-meta">
            <div className="ta-toast-label">{TOAST_LABELS[t.tone] || "Info"}</div>
            <div className="ta-toast-msg">{t.msg}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

/* ---- useToasts hook ------------------------------------------------------- */
function useToasts() {
  const [toasts, setToasts] = useState([]);
  const timers = useRef({});
  const push = (msg, tone = "ok", duration = 4000) => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev.slice(-4), { id, msg, tone }]);
    timers.current[id] = setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
      delete timers.current[id];
    }, duration);
  };
  useEffect(() => () => Object.values(timers.current).forEach(clearTimeout), []);
  return { toasts, push };
}

/* ==========================================================================
   MOCK DATA
   ========================================================================== */
const PERIOD_DATA = {
  "7d":  { label:"Past 7 days", outperf:0.4, pnl:{ total_pnl:84.2,profit_pct:0.84,realized_pnl:96,unrealized_pnl:-11.8,wins:3,losses:1,win_rate:75,open_count:5,closed_count:4,starting_capital:10000}, strategy:[10000,10018,10012,10042,10038,10064,10084].map((v,i)=>({date:["Mon","Tue","Wed","Thu","Fri","Mon","Tue"][i],value:v})), sp500:[10000,10008,10005,10018,10015,10022,10019].map((v,i)=>({date:["Mon","Tue","Wed","Thu","Fri","Mon","Tue"][i],value:v}))},
  "30d": { label:"Past 30 days", outperf:1.1, pnl:{ total_pnl:218.4,profit_pct:2.18,realized_pnl:280,unrealized_pnl:-61.6,wins:8,losses:3,win_rate:73,open_count:5,closed_count:11,starting_capital:10000}, strategy:[10000,10010,10008,10025,10018,10040,10035,10058,10060,10048,10080,10084].map((v,i)=>({date:`May ${i*2+1}`,value:v})), sp500:[10000,10005,10003,10012,10010,10020,10018,10025,10023,10020,10025,10019].map((v,i)=>({date:`May ${i*2+1}`,value:v}))},
  "1y":  { label:"Past year", outperf:2.9, pnl:{ total_pnl:420.18,profit_pct:4.20,realized_pnl:532.58,unrealized_pnl:-112.4,wins:17,losses:8,win_rate:68,open_count:5,closed_count:25,starting_capital:10000}, strategy:[10000,10020,9980,10060,10110,10090,10140,10200,10280,10310,10260,10420].map((v,i)=>({date:["Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar","Apr","May"][i],value:v})), sp500:[10000,10015,9990,10040,10080,10070,10100,10130,10180,10200,10175,10130].map((v,i)=>({date:["Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar","Apr","May"][i],value:v}))},
  "ytd": { label:"Year to date", outperf:1.8, pnl:{ total_pnl:328,profit_pct:3.28,realized_pnl:410,unrealized_pnl:-82,wins:14,losses:6,win_rate:70,open_count:5,closed_count:20,starting_capital:10000}, strategy:[10000,10040,10020,10090,10110,10084].map((v,i)=>({date:["Jan","Feb","Mar","Apr","May","Jun"][i],value:v})), sp500:[10000,10020,10010,10040,10050,10019].map((v,i)=>({date:["Jan","Feb","Mar","Apr","May","Jun"][i],value:v}))},
};

const MOCK = {
  status: { mode:"live_approval", kill_switch:false, market_open:true, starting_capital:10000, requires_approval:true, scheduler_running:true },
  pnl: { total_pnl:420.18, profit_pct:4.2, realized_pnl:532.58, unrealized_pnl:-112.4, open_count:5, closed_count:25, wins:17, losses:8, win_rate:68, starting_capital:10000 },
  buyingPower: { total:10000, used:3420, remaining:6580, pct_used:34.2 },
  benchmark: { outperformance_pct:2.9, strategy:PERIOD_DATA["1y"].strategy, sp500:PERIOD_DATA["1y"].sp500 },
  positions: [
    { id:1, symbol:"NVDA", strategy:"Short strangle", contracts:2, entry_credit:312, probability_of_profit:68, unrealized_pnl:84.2, dte_at_entry:41, status:"open", rationale:"IV rank 82 — elevated. 16Δ short strikes, liquid chain, no earnings in window. Sized to 4% BP." },
    { id:2, symbol:"AMD", strategy:"Put credit spread", contracts:3, entry_credit:156, probability_of_profit:71, unrealized_pnl:31.05, dte_at_entry:38, status:"open", rationale:"Defined-risk preferred at $10k working capital. IVR 64, tight bid/ask, OI > 5k." },
    { id:3, symbol:"TSLA", strategy:"Iron condor", contracts:1, entry_credit:224, probability_of_profit:64, unrealized_pnl:-52.1, dte_at_entry:22, status:"working", rationale:"Wide expected move on IVR 77. Symmetric 16Δ wings. Now at 21 DTE — flagged to roll." },
    { id:4, symbol:"META", strategy:"Naked put", contracts:1, entry_credit:188, probability_of_profit:70, unrealized_pnl:22.4, dte_at_entry:44, status:"open", rationale:"IVR 61, strong liquidity. 16Δ put, BP-friendly. Earnings cleared the blackout window." },
    { id:5, symbol:"AMZN", strategy:"Put credit spread", contracts:2, entry_credit:142, probability_of_profit:73, unrealized_pnl:36.85, dte_at_entry:40, status:"open", rationale:"IVR 58. Defined risk, 5-wide spread, 16Δ short. Below per-symbol concentration cap." },
    { id:6, symbol:"COIN", strategy:"Short strangle", contracts:1, entry_credit:198, probability_of_profit:65, unrealized_pnl:-18.4, dte_at_entry:35, status:"open", rationale:"IVR 74, crypto IV elevated. 16Δ strikes, small size given BP constraints." },
    { id:7, symbol:"SPY", strategy:"Put credit spread", contracts:4, entry_credit:88, probability_of_profit:74, unrealized_pnl:14.2, dte_at_entry:43, status:"open", rationale:"Low IVR (31) but highly liquid anchor. Defined risk, tight spread, OI > 50k." },
  ],
  closed: [
    { id:11, symbol:"AAPL", strategy:"Put credit spread", probability_of_profit:72, realized_pnl:96, entry_credit:184, profit_pct_taken:52, is_win:true, exit_reason:"Take-profit 50%",
      timeline:[{date:"May 12, 10:30",type:"opened",note:"Opened — IVR 67, 45 DTE, 16Δ short put, $184 credit."},{date:"May 28, 09:45",type:"exit",note:"Closed at take-profit (52%). Realized +$96."}]},
    { id:12, symbol:"GOOGL", strategy:"Short strangle", probability_of_profit:67, realized_pnl:142.5, entry_credit:268, profit_pct_taken:53, is_win:true, exit_reason:"Ahead-of-pace schedule",
      timeline:[{date:"Apr 30, 11:15",type:"opened",note:"Opened strangle — IVR 71, 45 DTE, 16Δ both sides, $268 credit."},{date:"May 14, 14:30",type:"managed",note:"Untested side rolled in for $22 additional credit after TSLA spike."},{date:"May 21, 10:00",type:"exit",note:"Ahead-of-pace close (53% of max in 21 days vs. 28-day average). Realized +$142.50."}]},
    { id:13, symbol:"NFLX", strategy:"Iron condor", probability_of_profit:65, realized_pnl:-88, entry_credit:176, profit_pct_taken:-50, is_win:false, exit_reason:"Rolled, then closed at 21 DTE",
      timeline:[{date:"Apr 15, 09:50",type:"opened",note:"Opened iron condor — IVR 69, 45 DTE, 16Δ short, $176 credit."},{date:"Apr 28, 13:20",type:"managed",note:"Call side tested. Rolled call spread up for $12 credit."},{date:"May 7, 09:35",type:"managed",note:"Rolled entire position out 30 days for $8 net credit."},{date:"May 22, 10:05",type:"exit",note:"21 DTE exit — closed for loss of $88. Position defended but challenged."}]},
    { id:14, symbol:"MSFT", strategy:"Naked put", probability_of_profit:70, realized_pnl:110, entry_credit:210, profit_pct_taken:52, is_win:true, exit_reason:"Take-profit 50%",
      timeline:[{date:"May 1, 10:00",type:"opened",note:"Opened naked put — IVR 63, 45 DTE, 16Δ short put, $210 credit."},{date:"May 19, 11:30",type:"exit",note:"Take-profit hit at 52%. Realized +$110."}]},
    { id:15, symbol:"COIN", strategy:"Short strangle", probability_of_profit:63, realized_pnl:-124, entry_credit:248, profit_pct_taken:-50, is_win:false, exit_reason:"Tested side, defended, closed",
      timeline:[{date:"Apr 20, 09:45",type:"opened",note:"Opened strangle — IVR 81, 45 DTE, 16Δ both sides, $248 credit."},{date:"May 2, 14:00",type:"managed",note:"Put side tested (COIN -18%). Rolled put down for $14 additional credit."},{date:"May 10, 11:45",type:"managed",note:"Rolled position out 21 days. Position still challenged."},{date:"May 20, 10:30",type:"exit",note:"Closed at 21 DTE for $124 loss. Could not recover."}]},
    { id:16, symbol:"SPY", strategy:"Put credit spread", probability_of_profit:74, realized_pnl:64, entry_credit:124, profit_pct_taken:52, is_win:true, exit_reason:"Take-profit 50%",
      timeline:[{date:"May 5, 10:15",type:"opened",note:"Opened put spread — IVR 38, 45 DTE, 16Δ short, $124 credit."},{date:"May 20, 14:00",type:"exit",note:"Take-profit at 52%. Realized +$64."}]},
    { id:17, symbol:"QQQ", strategy:"Iron condor", probability_of_profit:68, realized_pnl:88, entry_credit:162, profit_pct_taken:54, is_win:true, exit_reason:"Ahead-of-pace schedule",
      timeline:[{date:"Apr 22, 09:30",type:"opened",note:"Iron condor — IVR 58, 45 DTE, $162 credit."},{date:"May 8, 10:00",type:"exit",note:"Ahead-of-pace close at 54% in 16 days (avg 24 days). Realized +$88."}]},
    { id:18, symbol:"AMZN", strategy:"Call credit spread", probability_of_profit:69, realized_pnl:-76, entry_credit:138, profit_pct_taken:-55, is_win:false, exit_reason:"Rolled, closed at 21 DTE",
      timeline:[{date:"Apr 10, 11:00",type:"opened",note:"Opened call spread — IVR 72, 45 DTE, 16Δ short call, $138 credit."},{date:"Apr 25, 14:30",type:"managed",note:"Call tested after earnings beat. Rolled up for $18 credit."},{date:"May 5, 10:20",type:"exit",note:"21 DTE exit. Closed for $76 loss — rally continued above rolled strikes."}]},
  ],
  approvals: [
    { id:21, symbol:"NVDA", strategy:"Short strangle", contracts:2, entry_credit:312, probability_of_profit:68, rationale:"IV rank 82 — elevated. 16Δ short strikes, liquid chain, no earnings in window. Sized to 4% BP." },
    { id:22, symbol:"AMD", strategy:"Put credit spread", contracts:3, entry_credit:156, probability_of_profit:71, rationale:"Defined-risk at constrained BP. IVR 64, tight spread, OI > 5k. Within risk limits." },
    { id:23, symbol:"TSLA", strategy:"Iron condor", contracts:1, entry_credit:224, probability_of_profit:64, rationale:"IVR 77, wide expected move. Symmetric 16Δ wings, defined risk. BP cap: 2.2% of $10k." },
  ],
  watchlist: [
    { symbol:"NVDA", iv_rank:82, iv_pctile:88, liquidity:"A", source:"tt:High Options Volume", enabled:true, focus:true },
    { symbol:"TSLA", iv_rank:77, iv_pctile:81, liquidity:"A", source:"tt:High Options Volume", enabled:true, focus:true },
    { symbol:"COIN", iv_rank:74, iv_pctile:78, liquidity:"B", source:"custom", enabled:true, focus:true },
    { symbol:"AMD", iv_rank:64, iv_pctile:70, liquidity:"A", source:"tt:High Options Volume", enabled:true, focus:false },
    { symbol:"META", iv_rank:61, iv_pctile:66, liquidity:"A", source:"custom", enabled:true, focus:false },
    { symbol:"AMZN", iv_rank:58, iv_pctile:62, liquidity:"B", source:"tt:High Options Volume", enabled:true, focus:false },
    { symbol:"NFLX", iv_rank:44, iv_pctile:50, liquidity:"B", source:"custom", enabled:true, focus:false },
    { symbol:"QQQ", iv_rank:38, iv_pctile:44, liquidity:"A", source:"tt:Liquid ETFs", enabled:true, focus:false },
    { symbol:"AAPL", iv_rank:31, iv_pctile:40, liquidity:"A", source:"tt:High Options Volume", enabled:false, focus:false },
    { symbol:"SPY", iv_rank:12, iv_pctile:18, liquidity:"A", source:"default", enabled:true, focus:false },
  ],
  ttLists: [
    { name:"High Options Volume", count:194 },
    { name:"Liquid ETFs", count:38 },
    { name:"Earnings This Week", count:27 },
    { name:"S&P 100", count:100 },
    { name:"High IV Rank", count:61 },
    { name:"Tasty 250", count:250 },
  ],
  activity: [
    { id:101, time:"10:42:18", mode:"live_approval", considered:24, planned:3, placed:2, rejected:1, exits:1, universe:["NVDA","TSLA","AMD","META","AMZN"],
      commentary:"IVR elevated across semis. Opened NVDA strangle + AMD spread; rejected a TSLA condor — bid/ask width above the liquidity cap. Rolled the META put out to the next cycle at 21 DTE.",
      plannedList:[{symbol:"NVDA",strategy:"Short strangle",credit:312,pop:68},{symbol:"AMD",strategy:"Put credit spread",credit:156,pop:71},{symbol:"TSLA",strategy:"Iron condor",credit:224,pop:64}],
      placedList:[{symbol:"NVDA",strategy:"Short strangle",credit:312,pop:68},{symbol:"AMD",strategy:"Put credit spread",credit:156,pop:71}],
      rejectedList:[{symbol:"TSLA",strategy:"Iron condor",reason:"Bid/ask width 4.1% > 2% liquidity cap in cert quotes."}],
      managedList:[{symbol:"META",strategy:"Naked put",action:"Rolled out — 21 DTE reached",credit_change:18}]},
    { id:102, time:"09:35:02", mode:"live_approval", considered:24, planned:2, placed:1, rejected:1, exits:0, universe:["TSLA","COIN","NVDA","AMD","AMZN"],
      commentary:"Regime calm at the open. One AMZN put credit spread placed within BP caps; a COIN strangle rejected — earnings inside the blackout window.",
      plannedList:[{symbol:"AMZN",strategy:"Put credit spread",credit:142,pop:73},{symbol:"COIN",strategy:"Short strangle",credit:198,pop:65}],
      placedList:[{symbol:"AMZN",strategy:"Put credit spread",credit:142,pop:73}],
      rejectedList:[{symbol:"COIN",strategy:"Short strangle",reason:"Earnings event (Q2 results) within 7-day blackout window."}],
      managedList:[]},
    { id:103, time:"Yesterday 15:58", mode:"sandbox", considered:22, planned:1, placed:1, rejected:0, exits:2, universe:["AAPL","MSFT","SPY","META","GOOGL"],
      commentary:"End-of-day management pass. Took profit on AAPL spread (hit 50%) and MSFT put (ahead-of-pace). Opened one SPY spread into the close.",
      plannedList:[{symbol:"SPY",strategy:"Put credit spread",credit:88,pop:74}],
      placedList:[{symbol:"SPY",strategy:"Put credit spread",credit:88,pop:74}],
      rejectedList:[],
      managedList:[{symbol:"AAPL",strategy:"Put credit spread",action:"Closed at take-profit (52%)",credit_change:-96},{symbol:"MSFT",strategy:"Naked put",action:"Ahead-of-pace close (52% in 18 days)",credit_change:-110}]},
  ],
  strategies: [
    { id:"strangle", label:"Short Strangle", enabled:true, desc:"Sell OTM call + put. Widest credit, undefined risk. Preferred when IVR is elevated and BP is ample." },
    { id:"naked_put", label:"Naked Put", enabled:true, desc:"Sell OTM put. Bullish-neutral bias, high PoP, undefined risk. Used when bearish risk is acceptable." },
    { id:"put_spread", label:"Put Credit Spread", enabled:true, desc:"Short put + long put. Defined risk — preferred when BP is constrained (<$15k working capital)." },
    { id:"call_spread", label:"Call Credit Spread", enabled:false, desc:"Short call + long call. Defined risk, bearish-to-neutral. Disabled by default; enable when thesis calls for it." },
    { id:"iron_condor", label:"Iron Condor", enabled:true, desc:"Put spread + call spread combined. Defined risk, lower credit vs. strangle. Balanced neutral stance." },
  ],
};

Object.assign(window, {
  Icon, useLucide, fmtMoney, fmtMoney0, fmtPct, signClass,
  usePagination, Pagination,
  Pill, Toggle, Segmented, StatCard, BuyingPowerCard, Panel, EquityChart, ConfirmDialog,
  ToastStack, useToasts,
  MOCK, PERIOD_DATA,
});
