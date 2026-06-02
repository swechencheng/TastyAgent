/* Overview — at-a-glance dashboard (v2: date filter, buying power card) */
const PERIODS = [
  { id:"7d",  label:"7D" },
  { id:"30d", label:"30D" },
  { id:"1y",  label:"1Y" },
  { id:"ytd", label:"YTD" },
  { id:"custom", label:"Custom" },
];

function Overview({ data, onApprove, onReject, goTo }) {
  useLucide();
  const [period, setPeriod] = useState("1y");
  const [customFrom, setCustomFrom] = useState("");
  const [customTo, setCustomTo] = useState("");

  const pd = PERIOD_DATA[period] || PERIOD_DATA["1y"];
  const p = period === "custom" ? data.pnl : pd.pnl;
  const strategy = period === "custom" ? data.benchmark.strategy : pd.strategy;
  const sp500    = period === "custom" ? data.benchmark.sp500    : pd.sp500;
  const outperf  = period === "custom" ? data.benchmark.outperformance_pct : pd.outperf;
  const approvals = data.approvals;
  const bp = data.buyingPower;

  return (
    <div className="ta-screen">
      <h1 className="ta-page-title">Overview</h1>

      {/* Date filter */}
      <div className="ta-filter-bar">
        {PERIODS.map((p) => (
          <button key={p.id} className={`ta-filter-btn ${period === p.id ? "active" : ""}`} onClick={() => setPeriod(p.id)}>{p.label}</button>
        ))}
        {period === "custom" && (
          <div className="ta-custom-range">
            <input type="date" className="ta-input ta-date-input" value={customFrom} onChange={(e) => setCustomFrom(e.target.value)} />
            <span className="ta-muted" style={{ fontSize: 13 }}>to</span>
            <input type="date" className="ta-input ta-date-input" value={customTo} onChange={(e) => setCustomTo(e.target.value)} />
          </div>
        )}
        {period !== "custom" && <span className="ta-period-label">{pd.label}</span>}
      </div>

      {/* KPI row + BP card — auto-wraps to second row */}
      <div className="ta-kpi-row">
        <StatCard label="Total P/L" value={fmtMoney(p.total_pnl)} delta={fmtPct(p.profit_pct)} deltaTone={p.total_pnl >= 0 ? "up" : "down"} />
        <StatCard label="Realized" value={fmtMoney(p.realized_pnl)} deltaTone="up" delta="closed" />
        <StatCard label="Unrealized" value={fmtMoney(p.unrealized_pnl)} deltaTone={p.unrealized_pnl >= 0 ? "up" : "down"} delta="open" />
        <StatCard label="Win rate" value={`${p.win_rate}%`} sub={`${p.wins}W / ${p.losses}L`} />
        <StatCard label="Open / Closed" value={`${p.open_count} / ${p.closed_count}`} sub={`cap ${fmtMoney0(p.starting_capital)}`} />
        <BuyingPowerCard bp={bp} />
      </div>

      {/* Approval queue */}
      {approvals.length > 0 && (
        <Panel title={<span><Icon name="bell" size={16} /> Needs attention · {approvals.length} pending approval</span>} className="ta-attention">
          <div className="ta-approvals">
            {approvals.map((t) => (
              <div className="ta-approval" key={t.id}>
                <div className="ta-approval-top">
                  <div>
                    <div className="ta-approval-sym">{t.symbol} · {t.strategy}</div>
                    <div className="ta-approval-meta">{t.contracts} contracts · credit {fmtMoney0(t.entry_credit)}</div>
                  </div>
                  <Pill tone="gain">PoP {t.probability_of_profit}%</Pill>
                </div>
                <div className="ta-approval-why">{t.rationale}</div>
                <div className="ta-approval-actions">
                  <button className="ta-btn ta-btn-approve" onClick={() => onApprove(t)}>Approve</button>
                  <button className="ta-btn ta-btn-reject" onClick={() => onReject(t)}>Reject</button>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      )}

      {/* Equity chart */}
      <Panel title={<span><Icon name="trending-up" size={16} /> Equity vs. S&amp;P 500</span>}>
        <EquityChart strategy={strategy} sp500={sp500} outperf={outperf} />
      </Panel>

      <div className="ta-two-col">
        {/* Open positions snippet */}
        <Panel title="Open positions" action={<button className="ta-link" onClick={() => goTo("positions")}>View all <Icon name="arrow-right" size={14} /></button>}>
          <table className="ta-table">
            <thead><tr><th>Symbol</th><th>Strategy</th><th className="num">PoP</th><th className="num">Unreal.</th><th className="num">DTE</th></tr></thead>
            <tbody>
              {data.positions.slice(0, 5).map((t) => (
                <tr key={t.id}>
                  <td className="ta-sym">{t.symbol}</td>
                  <td className="ta-muted">{t.strategy}</td>
                  <td className="num">{t.probability_of_profit}%</td>
                  <td className={`num ${signClass(t.unrealized_pnl)}`}>{fmtMoney(t.unrealized_pnl)}</td>
                  <td className="num">{t.dte_at_entry}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>

        {/* Recent activity */}
        <Panel title="Recent activity" action={<button className="ta-link" onClick={() => goTo("activity")}>Log <Icon name="arrow-right" size={14} /></button>}>
          <div className="ta-recent">
            {data.activity.slice(0, 3).map((a) => (
              <div className="ta-recent-row" key={a.id}>
                <div className="ta-recent-time">{a.time}</div>
                <div>
                  <div className="ta-recent-counts">+{a.placed} opened · {a.exits} managed · {a.rejected} rejected</div>
                  <div className="ta-recent-note">{a.commentary}</div>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
}
window.Overview = Overview;
