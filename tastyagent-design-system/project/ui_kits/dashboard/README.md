# TastyAgent — Dashboard UI Kit

A high-fidelity, interactive recreation of the **TastyAgent control panel** — the single
surface the operator uses to *monitor* and *manage* the agent. Built to the brand & IA in
`docs/UI_REDESIGN_BRIEF.md`. It's a cosmetic prototype (mock data, no real API), assembled
from small reusable React components so screens can be recomposed for new designs.

## Run it

Open `index.html`. No build step — React + Babel + Lucide load from CDN, and
`../../colors_and_type.css` provides the tokens. Mock data lives in `components.jsx` (`MOCK`)
and mirrors the real API shapes (see brief §7).

## What's interactive
- **Routing** between Overview · Positions · Watchlist · Activity · Settings (sidebar nav).
- **Status bar:** mode selector (switching to a **live** mode triggers a typed-`LIVE` confirm),
  Auto on/off, live P/L, and a guarded **kill switch** (confirm dialog + engaged banner).
- **Run cycle** button with a spinner + completion toast.
- **Overview:** KPI row, equity-vs-S&P chart, approval queue (**Approve / Reject**), open-
  positions snippet, recent activity.
- **Positions:** Open/Closed segmented tabs, expandable rationale rows, win/loss badges.
- **Watchlist:** IV-rank heat bars, add ticker, enable toggles, remove, tastytrade import panel.
- **Activity:** expandable decision-log feed with Claude's commentary + universe chips.
- **Settings:** Agent / Strategy / Management / Risk groups with live derived effects, per-group
  save + "unsaved changes" state.
- **Toasts** on every mutating action.

## Files
| File | Role |
|---|---|
| `index.html` | Entry — loads tokens, libs, and every component, mounts `<App/>`. |
| `ui-kit.css` | All component styles (consumes `colors_and_type.css` tokens). |
| `components.jsx` | Primitives + `MOCK` data: `Icon`, `Pill`, `Toggle`, `Segmented`, `StatCard`, `Panel`, `EquityChart`, `ConfirmDialog`, `Toast`, formatters. Exports to `window`. |
| `AppShell.jsx` | `StatusBar`, `Sidebar`, and the `App` state machine (routing, mode/kill/auto, approvals, toasts). |
| `Overview.jsx` · `Positions.jsx` · `WatchlistScreen.jsx` · `Activity.jsx` · `Settings.jsx` | The five routed screens. |

## Reuse notes
- Each Babel `<script>` has its own scope; shared components are published to `window` at the
  end of `components.jsx`. Keep that pattern when adding files.
- All numbers go through `fmtMoney` / `fmtPct` and the `.ta-num` mono/tabular style.
- Icons: render `<Icon name="..."/>` and call `useLucide()` in the component so SVGs paint.

> Cosmetic recreation for design use — not production trading code, and not financial advice.
