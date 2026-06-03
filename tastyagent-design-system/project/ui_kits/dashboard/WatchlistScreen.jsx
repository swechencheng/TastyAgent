/* Watchlist — ranked table with pagination */
function WatchlistScreen({ data, toast }) {
  useLucide();
  const [rows, setRows] = useState(data.watchlist);
  const [newSym, setNewSym] = useState("");
  const [showImport, setShowImport] = useState(false);

  const sorted = [...rows].sort((a, b) => b.iv_rank - a.iv_rank);
  const pg = usePagination(sorted, 8);

  const add = () => {
    const s = newSym.trim().toUpperCase();
    if (!s || rows.some((r) => r.symbol === s)) return;
    setRows([...rows, { symbol:s, iv_rank:Math.floor(Math.random()*60)+20, iv_pctile:50, liquidity:"B", source:"custom", enabled:true, focus:false }]);
    setNewSym("");
    toast(`Added ${s} to the watchlist`);
  };
  const remove = (s) => { setRows(rows.filter((r) => r.symbol !== s)); toast(`Removed ${s}`); };
  const toggle = (s) => setRows(rows.map((r) => r.symbol === s ? { ...r, enabled:!r.enabled } : r));

  const heat = (ivr) => {
    const a = Math.max(0.12, ivr / 100);
    return { background:`rgba(228,0,43,${a.toFixed(2)})`, color: ivr > 45 ? "#fff" : "var(--text-muted)" };
  };

  return (
    <div className="ta-screen">
      <h1 className="ta-page-title">Watchlist</h1>
      <p className="ta-page-sub">{rows.length} symbols · seeded from tastytrade <b>High Options Volume</b>. The agent does the expensive work on the highest-IVR liquid names each cycle.</p>

      <div className="ta-toolbar">
        <input className="ta-input" placeholder="Add ticker (e.g. NFLX)" value={newSym}
          onChange={(e) => setNewSym(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && add()}
          style={{ width:200 }} />
        <button className="ta-btn ta-btn-primary" onClick={add}><Icon name="plus" size={16} />Add</button>
        <button className="ta-btn ta-btn-secondary" onClick={() => setShowImport(!showImport)}>
          <Icon name="list-plus" size={16} />Browse tastytrade lists
        </button>
      </div>

      <Panel>
        <table className="ta-table">
          <thead>
            <tr><th>Symbol</th><th>IV rank</th><th className="num">IV %ile</th><th>Liq</th><th>Source</th><th>In focus</th><th>Enabled</th><th></th></tr>
          </thead>
          <tbody>
            {pg.pageItems.map((w) => (
              <tr key={w.symbol} style={{ opacity: w.enabled ? 1 : 0.45 }}>
                <td className="ta-sym">{w.symbol}</td>
                <td>
                  <div className="ta-ivr">
                    <span className="ta-ivr-badge" style={heat(w.iv_rank)}>{w.iv_rank}</span>
                    <span className="ta-ivr-bar"><i style={{ width:`${w.iv_rank}%`, background:"var(--brand)" }} /></span>
                  </div>
                </td>
                <td className="num">{w.iv_pctile}%</td>
                <td>{w.liquidity}</td>
                <td><span className="ta-src">{w.source}</span></td>
                <td>{w.focus ? <Pill tone="brand">focus</Pill> : <span className="ta-muted">—</span>}</td>
                <td><Toggle on={w.enabled} onChange={() => toggle(w.symbol)} ariaLabel={`Enable ${w.symbol}`} /></td>
                <td><button className="ta-icon-btn" aria-label={`Remove ${w.symbol}`} onClick={() => remove(w.symbol)}><Icon name="trash-2" size={16} /></button></td>
              </tr>
            ))}
          </tbody>
        </table>
        <Pagination page={pg.page} pageCount={pg.pageCount} onPage={pg.setPage} />
      </Panel>

      {showImport && (
        <Panel title="tastytrade recommended lists">
          <table className="ta-table">
            <thead><tr><th>List</th><th className="num">Symbols</th><th></th></tr></thead>
            <tbody>
              {data.ttLists.map((l) => (
                <tr key={l.name}>
                  <td className="ta-sym" style={{ fontWeight:500 }}>{l.name}</td>
                  <td className="num">{l.count}</td>
                  <td><button className="ta-btn ta-btn-secondary ta-btn-sm" onClick={() => toast(`Imported ${l.count} symbols from ${l.name}`)}>Import all</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>
      )}
    </div>
  );
}
window.WatchlistScreen = WatchlistScreen;
