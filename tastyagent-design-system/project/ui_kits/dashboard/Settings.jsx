/* Settings — tabbed groups + strategy toggles */
function Field({ label, help, unit, derived, children }) {
  return (
    <div className="ta-field">
      <div className="ta-field-main">
        <div>
          <div className="ta-field-label">{label}</div>
          {help && <div className="ta-field-help">{help}</div>}
        </div>
        <div className="ta-field-control">
          {children}
          {unit && <span className="ta-field-unit">{unit}</span>}
        </div>
      </div>
      {derived && <div className="ta-field-derived">{derived}</div>}
    </div>
  );
}

function NInput({ value, onChange, w = 88 }) {
  return <input className="ta-input ta-num-input" type="number" value={value} style={{ width:w }} onChange={(e) => onChange(+e.target.value)} />;
}

function SaveBar({ dirty, onSave }) {
  if (!dirty) return <span className="ta-saved"><Icon name="check" size={14} />Saved</span>;
  return <button className="ta-btn ta-btn-primary ta-btn-sm" onClick={onSave}>Save changes</button>;
}

const SETTING_TABS = [
  { id:"agent",      label:"Agent",           icon:"bot" },
  { id:"strategies", label:"Strategies",      icon:"target" },
  { id:"strategy",   label:"Strategy params", icon:"sliders-horizontal" },
  { id:"management", label:"Management",      icon:"hand-coins" },
  { id:"risk",       label:"Risk limits",     icon:"shield" },
];

function Settings({ data, toast, onModeChange }) {
  useLucide();
  const [activeTab, setActiveTab] = useState("agent");
  const cap = 10000;
  const [s, setS] = useState({
    capital:cap, scheduler:true, interval:30, marketHours:true,
    minIvr:30, dteMin:30, dteTarget:45, dteMax:60, shortDelta:16, topN:8,
    takeProfit:50, manageDte:21, hardStop:false, stopMult:2,
    bpPerTrade:5, bpTotal:40, maxPos:12, maxPerSym:2, dailyHalt:5,
  });
  const [savedSnap, setSavedSnap] = useState(JSON.stringify(s));
  const [strategies, setStrategies] = useState(data.strategies);

  const set = (k, v) => setS((p) => ({ ...p, [k]:v }));
  const isDirty = JSON.stringify(s) !== savedSnap;
  const save = () => { setSavedSnap(JSON.stringify(s)); toast("Settings saved"); };
  const toggleStrategy = (id) => setStrategies((prev) => prev.map((st) => st.id === id ? { ...st, enabled:!st.enabled } : st));

  return (
    <div className="ta-screen">
      <h1 className="ta-page-title">Settings</h1>
      <p className="ta-page-sub">Manage the agent end-to-end. Sensitive changes are confirmed; risk changes are saved per group.</p>

      {/* Tab bar */}
      <div className="ta-settings-tabs">
        {SETTING_TABS.map((t) => (
          <button key={t.id} className={`ta-settings-tab ${activeTab === t.id ? "active" : ""}`} onClick={() => setActiveTab(t.id)}>
            <Icon name={t.icon} size={16} />{t.label}
          </button>
        ))}
      </div>

      {/* Agent tab */}
      {activeTab === "agent" && (
        <Panel title={<span><Icon name="bot" size={16} /> Agent</span>} action={<SaveBar dirty={isDirty} onSave={save} />}>
          <div className="ta-fields">
            <Field label="Trading mode" help="Switching to a live mode requires a typed confirm.">
              <Segmented value={data.status.mode}
                options={[{value:"sandbox",label:"Sandbox"},{value:"live_approval",label:"Live-approval"},{value:"live_auto",label:"Live-auto"}]}
                onChange={onModeChange} />
            </Field>
            <Field label="Working capital" help="Capital the agent sizes positions against." unit="$"
              derived={`Per-trade BP cap = ${s.bpPerTrade}% × ${fmtMoney0(s.capital)} = ${fmtMoney0(Math.round(s.capital * s.bpPerTrade / 100))}`}>
              <NInput value={s.capital} onChange={(v) => set("capital", v)} w={104} />
            </Field>
            <Field label="Scheduler" help="Run the decision loop automatically during market hours.">
              <Toggle on={s.scheduler} onChange={(v) => set("scheduler", v)} ariaLabel="Scheduler" />
            </Field>
            <Field label="Cycle interval" help="How often the loop ticks during market hours." unit="min">
              <NInput value={s.interval} onChange={(v) => set("interval", v)} />
            </Field>
            <Field label="Market hours only" help="When on, the scheduler won't fire outside regular hours.">
              <Toggle on={s.marketHours} onChange={(v) => set("marketHours", v)} ariaLabel="Market hours only" />
            </Field>
          </div>
        </Panel>
      )}

      {/* Strategies tab */}
      {activeTab === "strategies" && (
        <Panel title={<span><Icon name="target" size={16} /> Strategies</span>}>
          <div className="ta-fields">
            {strategies.map((st) => (
              <Field key={st.id} label={st.label} help={st.desc}>
                <Toggle on={st.enabled} onChange={() => toggleStrategy(st.id)} ariaLabel={`Enable ${st.label}`} />
              </Field>
            ))}
          </div>
        </Panel>
      )}

      {/* Strategy params tab */}
      {activeTab === "strategy" && (
        <Panel title={<span><Icon name="sliders-horizontal" size={16} /> Strategy params</span>} action={<SaveBar dirty={isDirty} onSave={save} />}>
          <div className="ta-fields">
            <Field label="Min IV rank" help="Only sell premium when IV rank is at least this high." unit="IVR">
              <NInput value={s.minIvr} onChange={(v) => set("minIvr", v)} />
            </Field>
            <Field label="DTE window (min / target / max)" help="Days-to-expiration range for new positions.">
              <span className="ta-dte-group">
                <NInput value={s.dteMin} onChange={(v) => set("dteMin", v)} w={64} />
                <NInput value={s.dteTarget} onChange={(v) => set("dteTarget", v)} w={64} />
                <NInput value={s.dteMax} onChange={(v) => set("dteMax", v)} w={64} />
              </span>
            </Field>
            <Field label="Target short delta" help="Strike selection for short legs (≈16Δ ≈ 68% PoP)." unit="Δ">
              <NInput value={s.shortDelta} onChange={(v) => set("shortDelta", v)} />
            </Field>
            <Field label="Universe top-N" help="How many highest-IVR names get chain work each cycle." unit="names">
              <NInput value={s.topN} onChange={(v) => set("topN", v)} />
            </Field>
          </div>
        </Panel>
      )}

      {/* Management / Exits tab */}
      {activeTab === "management" && (
        <Panel title={<span><Icon name="hand-coins" size={16} /> Management / Exits</span>} action={<SaveBar dirty={isDirty} onSave={save} />}>
          <div className="ta-fields">
            <Field label="Take-profit" help="Close a winner at this % of max profit." unit="%">
              <NInput value={s.takeProfit} onChange={(v) => set("takeProfit", v)} />
            </Field>
            <Field label="Manage at DTE" help="Roll out / defend when a position reaches this DTE." unit="DTE">
              <NInput value={s.manageDte} onChange={(v) => set("manageDte", v)} />
            </Field>
            <Field label="Use hard stop" help="Off by default — tastytrade manages rather than stops out.">
              <Toggle on={s.hardStop} onChange={(v) => set("hardStop", v)} ariaLabel="Hard stop" />
            </Field>
            <Field label="Stop-loss multiple" help="Stop at this multiple of credit received (when hard stop is on)." unit="×">
              <NInput value={s.stopMult} onChange={(v) => set("stopMult", v)} />
            </Field>
          </div>
        </Panel>
      )}

      {/* Risk limits tab */}
      {activeTab === "risk" && (
        <Panel title={<span><Icon name="shield" size={16} /> Risk limits</span>} action={<SaveBar dirty={isDirty} onSave={save} />}>
          <div className="ta-fields">
            <Field label="Max per-trade BP" help="Buying power cap for any single trade." unit="%"
              derived={`= ${fmtMoney0(Math.round(s.capital * s.bpPerTrade / 100))} at ${fmtMoney0(s.capital)} capital`}>
              <NInput value={s.bpPerTrade} onChange={(v) => set("bpPerTrade", v)} />
            </Field>
            <Field label="Max total BP" help="Portfolio-wide buying power cap." unit="%">
              <NInput value={s.bpTotal} onChange={(v) => set("bpTotal", v)} />
            </Field>
            <Field label="Max positions" help="Hard cap on concurrent open positions." unit="open">
              <NInput value={s.maxPos} onChange={(v) => set("maxPos", v)} />
            </Field>
            <Field label="Max positions / symbol" help="Concentration cap per underlying." unit="per sym">
              <NInput value={s.maxPerSym} onChange={(v) => set("maxPerSym", v)} />
            </Field>
            <Field label="Daily-loss halt" help="Halt all new entries if daily loss exceeds this." unit="%">
              <NInput value={s.dailyHalt} onChange={(v) => set("dailyHalt", v)} />
            </Field>
          </div>
        </Panel>
      )}
    </div>
  );
}
window.Settings = Settings;
