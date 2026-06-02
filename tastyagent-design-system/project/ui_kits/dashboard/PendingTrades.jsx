/* PendingTrades — approval queue with compact stat row (v2) */
function PendingTrades({ data, onApprove, onReject, approvedCount, rejectedCount }) {
  useLucide();
  const pg = usePagination(data.approvals, 8);
  const bp = data.buyingPower;
  const bpAfter = bp.remaining - data.approvals.reduce((sum, t) => sum + (t.entry_credit * t.contracts * 0.2), 0);

  if (data.approvals.length === 0) {
    return (
      <div className="ta-screen">
        <h1 className="ta-page-title">Pending Trades</h1>
        <div className="ta-stat-row">
          <BuyingPowerCard bp={bp} />
          <div className="ta-stat">
            <div className="ta-stat-label">Approved this session</div>
            <div className="ta-stat-value ta-gain">{approvedCount}</div>
            <span className="ta-delta up">▲ trades sent to broker</span>
          </div>
          <div className="ta-stat">
            <div className="ta-stat-label">Rejected this session</div>
            <div className="ta-stat-value" style={{ color: approvedCount > 0 && rejectedCount === 0 ? "var(--text)" : "var(--loss)" }}>{rejectedCount}</div>
            <span className="ta-delta flat">• skipped by you</span>
          </div>
        </div>
        <div className="ta-empty-state">
          <Icon name="inbox" size={40} style={{ color:"var(--text-faint)", marginBottom:12 }} />
          <div>No pending trades.</div>
          <div style={{ color:"var(--text-faint)", fontSize:13, marginTop:6 }}>
            Trades will appear here when running in Live-approval mode.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="ta-screen">
      <h1 className="ta-page-title">Pending Trades</h1>
      <p className="ta-page-sub">{data.approvals.length} trade{data.approvals.length > 1 ? "s" : ""} waiting for your approval.</p>

      {/* Compact stat row — 4 cards, flex-wrap, no stretch */}
      <div className="ta-stat-row">
        <BuyingPowerCard bp={bp} />
        <div className="ta-stat">
          <div className="ta-stat-label">BP if all approved</div>
          <div className="ta-stat-value">{fmtMoney0(bpAfter)}</div>
          <span className="ta-delta down">▼ estimated impact</span>
        </div>
        <div className="ta-stat">
          <div className="ta-stat-label">Approved this session</div>
          <div className="ta-stat-value ta-gain">{approvedCount}</div>
          <span className="ta-delta up">▲ sent to broker</span>
        </div>
        <div className="ta-stat">
          <div className="ta-stat-label">Rejected this session</div>
          <div className={`ta-stat-value ${rejectedCount > 0 ? "ta-loss" : ""}`}>{rejectedCount}</div>
          <span className="ta-delta flat">• skipped by you</span>
        </div>
      </div>

      {/* Approval cards */}
      <div className="ta-approvals">
        {pg.pageItems.map((t) => (
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
      <Pagination page={pg.page} pageCount={pg.pageCount} onPage={pg.setPage} />
    </div>
  );
}
window.PendingTrades = PendingTrades;
