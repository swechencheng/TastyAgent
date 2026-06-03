/* Positions — Open / Closed with pagination + closed timeline */
function TradeTimeline({ timeline }) {
  return (
    <div className="ta-timeline">
      {timeline.map((e, i) => (
        <div className="ta-tl-row" key={i}>
          <div className="ta-tl-rail">
            <span className={`ta-tl-dot ta-tl-${e.type}`} />
            {i < timeline.length - 1 && <span className="ta-tl-line" />}
          </div>
          <div className="ta-tl-body">
            <div className="ta-tl-date">{e.date}</div>
            <div className="ta-tl-note">{e.note}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

function ProfitBar({ pct }) {
  const abs = Math.abs(pct);
  const color = pct >= 0 ? "var(--gain)" : "var(--loss)";
  return (
    <div className="ta-profit-cell">
      <span className="ta-profit-pct" style={{ color }}>{pct > 0 ? "+" : "−"}{abs.toFixed(0)}%</span>
      <div className="ta-profit-track">
        <div className="ta-profit-fill" style={{ width: `${Math.min(abs, 100)}%`, background: color }} />
      </div>
    </div>
  );
}

function Positions({ data }) {
  useLucide();
  const [tab, setTab] = useState("open");
  const [expanded, setExpanded] = useState(null);

  const openPg = usePagination(data.positions, 6);
  const closedPg = usePagination(data.closed, 6);

  const toggleExpand = (id) => setExpanded(expanded === id ? null : id);

  return (
    <div className="ta-screen">
      <h1 className="ta-page-title">Positions</h1>
      <div className="ta-toolbar">
        <Segmented
          options={[{ value:"open", label:`Open · ${data.positions.length}` }, { value:"closed", label:`Closed · ${data.closed.length}` }]}
          value={tab}
          onChange={(v) => { setTab(v); setExpanded(null); }}
        />
      </div>

      {tab === "open" ? (
        <Panel>
          <table className="ta-table">
            <thead>
              <tr>
                <th>Symbol</th><th>Strategy</th><th className="num">Qty</th><th className="num">Credit</th>
                <th className="num">PoP</th><th className="num">Unreal.</th><th className="num">DTE</th><th>Status</th><th></th>
              </tr>
            </thead>
            <tbody>
              {openPg.pageItems.map((t) => (
                <React.Fragment key={t.id}>
                  <tr className="ta-row-click" onClick={() => toggleExpand(t.id)}>
                    <td className="ta-sym">{t.symbol}</td>
                    <td className="ta-muted">{t.strategy}</td>
                    <td className="num">{t.contracts}</td>
                    <td className="num">{fmtMoney0(t.entry_credit)}</td>
                    <td className="num">{t.probability_of_profit}%</td>
                    <td className={`num ${signClass(t.unrealized_pnl)}`}>{fmtMoney(t.unrealized_pnl)}</td>
                    <td className="num">{t.dte_at_entry <= 22 ? <span className="ta-warn-text">{t.dte_at_entry}</span> : t.dte_at_entry}</td>
                    <td><Pill tone={t.status === "open" ? "neutral" : "warn"}>{t.status}</Pill></td>
                    <td><Icon name={expanded === t.id ? "chevron-up" : "chevron-down"} size={16} /></td>
                  </tr>
                  {expanded === t.id && (
                    <tr className="ta-expand">
                      <td colSpan={9}>
                        <span className="ta-muted" style={{ fontSize:12 }}>Rationale · </span>
                        <span style={{ fontSize:13 }}>{t.rationale}</span>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
          <Pagination page={openPg.page} pageCount={openPg.pageCount} onPage={openPg.setPage} />
        </Panel>
      ) : (
        <Panel>
          <table className="ta-table">
            <thead>
              <tr>
                <th>Symbol</th><th>Strategy</th><th className="num">PoP</th>
                <th className="num">Realized</th><th>% Taken</th><th>Result</th><th>Exit reason</th><th></th>
              </tr>
            </thead>
            <tbody>
              {closedPg.pageItems.map((t) => (
                <React.Fragment key={t.id}>
                  <tr className="ta-row-click" onClick={() => toggleExpand(t.id)}>
                    <td className="ta-sym">{t.symbol}</td>
                    <td className="ta-muted">{t.strategy}</td>
                    <td className="num">{t.probability_of_profit}%</td>
                    <td className={`num ${t.is_win ? "ta-gain" : "ta-loss"}`}>{fmtMoney(t.realized_pnl)}</td>
                    <td><ProfitBar pct={t.profit_pct_taken} /></td>
                    <td><Pill tone={t.is_win ? "win" : "loss"}>{t.is_win ? "WIN" : "LOSS"}</Pill></td>
                    <td className="ta-muted" style={{ fontSize:12 }}>{t.exit_reason}</td>
                    <td><Icon name={expanded === t.id ? "chevron-up" : "chevron-down"} size={16} /></td>
                  </tr>
                  {expanded === t.id && (
                    <tr className="ta-expand">
                      <td colSpan={8} style={{ padding:"16px 16px 20px" }}>
                        <div style={{ fontSize:11, textTransform:"uppercase", letterSpacing:"0.05em", color:"var(--text-faint)", marginBottom:12 }}>Trade timeline</div>
                        <TradeTimeline timeline={t.timeline} />
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
          <Pagination page={closedPg.page} pageCount={closedPg.pageCount} onPage={closedPg.setPage} />
        </Panel>
      )}
    </div>
  );
}
window.Positions = Positions;
