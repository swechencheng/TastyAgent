/* Activity — decision log with expanded per-cycle trade breakdown */
function TradeList({ trades, tone, emptyText }) {
  if (!trades || trades.length === 0) return <div className="ta-act-empty">{emptyText}</div>;
  return (
    <table className="ta-table ta-act-table">
      <thead>
        <tr>
          <th>Symbol</th><th>Strategy</th>
          {trades[0].credit !== undefined && <th className="num">Credit</th>}
          {trades[0].pop !== undefined && <th className="num">PoP</th>}
          {trades[0].reason !== undefined && <th>Reason</th>}
          {trades[0].action !== undefined && <th>Action</th>}
          {trades[0].credit_change !== undefined && <th className="num">Credit Δ</th>}
        </tr>
      </thead>
      <tbody>
        {trades.map((t, i) => (
          <tr key={i}>
            <td className="ta-sym">{t.symbol}</td>
            <td className="ta-muted">{t.strategy}</td>
            {t.credit !== undefined && <td className="num">{fmtMoney0(t.credit)}</td>}
            {t.pop !== undefined && <td className="num">{t.pop}%</td>}
            {t.reason !== undefined && <td className={`ta-muted`} style={{ fontSize:12 }}>{t.reason}</td>}
            {t.action !== undefined && <td className="ta-muted" style={{ fontSize:12 }}>{t.action}</td>}
            {t.credit_change !== undefined && <td className={`num ${t.credit_change > 0 ? "ta-gain" : "ta-loss"}`}>{t.credit_change > 0 ? "+" : "−"}${Math.abs(t.credit_change)}</td>}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function Activity({ data }) {
  useLucide();
  const [open, setOpen] = useState(data.activity[0]?.id ?? null);
  const [activeTab, setActiveTab] = useState("placed");

  const tabs = (a) => [
    { id:"planned",  label:`Planned · ${a.plannedList.length}`,  tone:"neutral" },
    { id:"placed",   label:`Placed · ${a.placedList.length}`,    tone:"gain" },
    { id:"rejected", label:`Rejected · ${a.rejectedList.length}`,tone:"loss" },
    { id:"managed",  label:`Managed · ${a.managedList.length}`,  tone:"warn" },
  ];

  return (
    <div className="ta-screen">
      <h1 className="ta-page-title">Activity</h1>
      <p className="ta-page-sub">Every decision cycle — LLM commentary and the exact trades planned, placed, rejected, and managed.</p>

      <div className="ta-feed">
        {data.activity.map((a) => (
          <div className="ta-feed-item" key={a.id}>
            <div className="ta-feed-rail">
              <span className="ta-feed-dot" />
            </div>
            <div className="ta-feed-body">
              <div className="ta-feed-head" onClick={() => setOpen(open === a.id ? null : a.id)}>
                <div className="ta-feed-time">{a.time}<Pill tone="neutral" className="ta-feed-mode">{a.mode}</Pill></div>
                <div className="ta-feed-stats">
                  <span><b>{a.considered}</b> considered</span>
                  <span><b>{a.planned}</b> planned</span>
                  <span className="ta-gain"><b>{a.placed}</b> placed</span>
                  <span className="ta-loss"><b>{a.rejected}</b> rejected</span>
                  <span className="ta-warn-text"><b>{a.exits}</b> managed</span>
                  <Icon name={open === a.id ? "chevron-up" : "chevron-down"} size={16} />
                </div>
              </div>

              <div className="ta-feed-note">{a.commentary}</div>

              {open === a.id && (
                <div className="ta-feed-detail">
                  {/* Universe */}
                  <div className="ta-feed-section">
                    <div className="ta-feed-label">Universe analyzed (top {a.universe.length})</div>
                    <div className="ta-chip-row">
                      {a.universe.map((s) => <span className="ta-chip" key={s}>{s}</span>)}
                    </div>
                  </div>

                  {/* Trade breakdown tabs */}
                  <div className="ta-act-tabs">
                    {tabs(a).map((t) => (
                      <button key={t.id}
                        className={`ta-act-tab ${activeTab === t.id ? "active" : ""} ta-act-tab-${t.tone}`}
                        onClick={() => setActiveTab(t.id)}>
                        {t.label}
                      </button>
                    ))}
                  </div>

                  {activeTab === "planned"  && <TradeList trades={a.plannedList}  emptyText="None planned this cycle." />}
                  {activeTab === "placed"   && <TradeList trades={a.placedList}   emptyText="No trades placed." />}
                  {activeTab === "rejected" && <TradeList trades={a.rejectedList} emptyText="No rejections." />}
                  {activeTab === "managed"  && <TradeList trades={a.managedList}  emptyText="No management actions." />}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
window.Activity = Activity;
