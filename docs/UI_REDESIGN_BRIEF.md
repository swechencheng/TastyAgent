# TastyAgent — UI Redesign Brief

> Hand this whole document to a design tool / LLM to generate the new UI. It is
> self-contained: it covers the product, brand, information architecture, every screen,
> every data field (mapped to the real API), the new settings surface, and the
> implementation constraints.

---

## 1. Product context

**TastyAgent** is an AI options-trading agent that trades tastytrade's premium-selling
methodology. Deterministic tastytrade mechanics are hard guardrails; an OpenRouter LLM is an adaptive
selection layer *within* those rails. It paper-trades through tastytrade's sandbox and
(optionally) trades live with one-click approval.

**The user** is a single operator (the trader) running their own agent. They need to
**monitor** it (is it making money, what's open, what did it decide and why) and
**manage** it (mode, risk, strategy settings, watchlist, kill switch) — calmly and quickly,
often glancing at it during the trading day.

**This is a serious, data-dense financial control panel** — not a marketing site. Think
Bloomberg/trading-terminal clarity, not playful SaaS. Calm by default; loud only when
something needs attention (a loss, a pending approval, the kill switch).

---

## 2. Redesign goals

1. **One cohesive app** to both *monitor* and *manage* the agent (today these are scattered
   on one long scrolling page).
2. **Manage all settings from the UI** — trading mode, kill switch, scheduler, working
   capital, strategy params, risk limits, watchlist (most of these aren't editable today).
3. **Clear information hierarchy** — the most important state (P/L, status, anything needing
   action) is visible at a glance; detail is one click away.
4. **tastytrade-branded** — black, white, and tastytrade red.
5. **Trustworthy** — destructive/risky actions (kill switch, mode → live, settings changes)
   are explicit and confirmed; nothing surprising.

**Non-goals:** charting/TA tooling, multi-user/teams, mobile-native app (responsive web is
enough), backtesting (intentionally out of scope — paper trading is the validation).

---

## 3. Brand & visual identity

### Theme: dark, tastytrade black / white / red

Pure-black canvas, white content, tastytrade red as the brand/action/danger accent. Gains are
green, losses are red (semantically aligned with the brand red). Disambiguate "brand red CTA"
from "red loss number" by **form**: red *fills* = actions; red *text* = negative values.

### Color palette (exact hex)

| Token | Hex | Use |
|---|---|---|
| `bg` (canvas) | `#0A0A0B` | App background (near-black; pure `#000` for the deepest header/sidebar) |
| `surface` | `#141417` | Cards / panels raised off the canvas |
| `surface-2` | `#1C1C21` | Inputs, nested rows, hover fills |
| `border` | `#2A2A30` | Hairline borders / dividers |
| `text` | `#FFFFFF` | Primary text, key numbers |
| `text-muted` | `#9A9AA4` | Labels, secondary text (meets 4.5:1 on canvas) |
| `text-faint` | `#6B6B74` | Tertiary / disabled |
| **`brand`** (tastytrade red) | `#E4002B` | Logo, primary CTA fills, active nav, danger fills. *Verify exact hue against the live tastytrade brand; ~`#E4002B`/`#ED1C24`.* |
| `brand-hover` | `#FF1F47` | CTA hover |
| `loss` (text) | `#FF4D6A` | Negative P/L **text** (brighter than brand for 4.5:1 contrast on dark) |
| `gain` (text) | `#16C784` | Positive P/L text |
| `gain-soft` / `loss-soft` | `#16C78422` / `#FF4D6A22` | Subtle tints behind gain/loss chips, sparkline fills |
| `warn` | `#F0A500` | Cautions (e.g. near-DTE, approval pending) |
| `info` | `#4C9AFF` | Neutral highlights / links (use sparingly; keep red as the hero accent) |

**Contrast rule (from design guidelines):** every text/background pair ≥ 4.5:1. That's why
loss *text* uses the brighter `#FF4D6A`, while the deep `brand` red is for fills with white text.

### Typography

- **UI / headings:** **Inter** (or Geist Sans) — clean, neutral, financial.
- **Numbers / tables:** **JetBrains Mono** (or Inter with `font-variant-numeric: tabular-nums`)
  so prices, P/L, deltas, and percentages align in columns.
- Sizes: page title 20–24px; section 15–16px uppercase-tracked labels; body 14px; table 13–14px;
  big KPI numbers 28–34px. Line-height 1.5 for prose. Min 16px on mobile inputs.

### Iconography, shape, motion

- **Lucide** SVG icons only (no emoji). 20–24px, 1.5px stroke.
- Radius: 12px cards, 8px inputs/buttons, 999px pills.
- Elevation by surface color + 1px border (avoid heavy shadows on black; a subtle
  `0 1px 0 rgba(255,255,255,0.03)` top-highlight is enough).
- Motion: 150–250ms color/opacity transitions; `transform`/`opacity` only; respect
  `prefers-reduced-motion`. A small pulsing dot for "live/auto on".

---

## 4. Information architecture

A persistent **left sidebar** + a persistent **top status bar**, with a routed content area.

```
┌───────────────────────────────────────────────────────────────────────┐
│ STATUS BAR  ● TastyAgent | mode▾ | Market: Open | Auto●ON | P/L +$420  ⛔│
├──────────┬────────────────────────────────────────────────────────────┤
│ SIDEBAR  │  ROUTED CONTENT                                             │
│ Overview │                                                             │
│ Positions│                                                             │
│ Watchlist│                                                             │
│ Activity │                                                             │
│ Settings │                                                             │
│          │                                                             │
│ [Run     │                                                             │
│  cycle]  │                                                             │
└──────────┴────────────────────────────────────────────────────────────┘
```

**Top status bar (always visible, the mission-control strip):**
- Logo "Tasty<span red>Agent</span>", market open/closed pill, **mode selector**,
  **Auto on/off**, **total P/L** (color-coded), and a guarded **Kill switch** (far right,
  red, requires confirm). A small "live • updated 3s ago" indicator.

**Sidebar nav (pages):** Overview · Positions · Watchlist · Activity · Settings. A primary
**Run cycle** button pinned at the bottom (with a spinner state while running).

**Responsive:** sidebar collapses to a bottom tab bar / hamburger under 768px; status bar
wraps; tables become horizontally scrollable cards.

---

## 5. Screens (page-by-page)

### 5.1 Overview (the at-a-glance dashboard)
- **KPI row** (stat cards, each: label, big tabular number, delta, optional sparkline):
  Total P/L, Profit %, Realized, Unrealized, Win rate (with `W/L`), Open / Closed counts.
  Working capital shown as context.
- **Equity vs S&P 500** line chart (two series: TastyAgent = brand red, S&P = muted grey/white;
  tooltip, "outperformance +x%"). Empty state until snapshots accrue.
- **Needs attention**: if `requires_approval` and the queue is non-empty, a prominent
  **Approval queue** block (cards with symbol, strategy, contracts, credit, PoP, rationale,
  Approve / Reject — both confirmed). Hidden when empty.
- **Open positions** compact table (top 5, link to Positions page).
- **Recent activity** (last few decisions: time, "+2 opened / 1 rolled", one-line commentary).

### 5.2 Positions
- Tabs / segmented control: **Open** · **Closed (Win/Loss)**.
- **Open** table: Symbol, Strategy, Qty, Entry credit, **PoP**, Unrealized P/L (color), DTE,
  status (working/open), Rationale (truncated, expandable), per-row manage (close/roll — future).
- **Closed** table: Symbol, Strategy, PoP, Realized P/L (color), Win/Loss badge, Exit reason.
- Filters: by symbol, strategy, win/loss. Sortable columns. Sticky header, tabular nums.

### 5.3 Watchlist (the agent's universe)
- Header: count + "seeded from tastytrade High Options Volume". Add-ticker input + **Add**.
- Table: Symbol, **IV rank** (heat-tinted bar/badge — high IVR = stronger red tint),
  IV %ile, Liquidity rating, Source (custom / default / `tt:<list>`), **Enabled** toggle, Remove.
  Sorted by IV rank desc (where the agent will focus). Show which top-N are "in focus" this cycle.
- **Browse tastytrade lists**: opens a panel/modal listing their ~53 public lists (name + symbol
  count) with **Import all** per list.

### 5.4 Activity / Decision log
- Reverse-chronological feed of cycles. Each entry: timestamp, mode, **LLM commentary**
  (the "why"), counts (considered / planned / placed / rejected / exits-rolled), and the
  universe analyzed (top-N tickers). Expand to see the trades placed/rejected with reasons.
  *(Backend: needs a decisions/activity endpoint — see §7.)*

### 5.5 Settings (the management surface — mostly NEW)
Grouped, with inline help, sensible min/max, and **confirmation for sensitive changes**
(anything that loosens risk, or switching to a live mode). Save per-group with a clear
"unsaved changes" state. Groups:

- **Agent**: Trading mode (segmented: Sandbox / Live-approval / Live-auto — switching to a
  live mode requires a typed confirm), Working capital ($), Scheduler (on/off + interval +
  market-hours-only), Kill switch.
- **Strategy** (mirrors `StrategyParams`): min IV rank, DTE window (min/target/max), target
  short delta, spread long delta, max short-leg delta, liquidity (max bid/ask width %, min OI,
  min volume), earnings blackout days, **universe top-N**.
- **Management/Exits**: take-profit %, manage-at-DTE, tested-delta threshold, use-hard-stop
  (toggle, default off), stop-loss multiple.
- **Risk** (mirrors `RiskLimits`): max per-trade BP %, max total BP %, max positions,
  max positions/symbol, daily-loss-halt %, consecutive-loss halt.

Each setting: label, current value, control (number/slider/toggle/segmented), unit, and a
one-line "what this does." Show derived effects live (e.g. "per-trade BP cap = 5% × $10,000 =
$500").

---

## 6. Component patterns

- **Stat / KPI card** — label, big tabular number, delta chip (gain/loss colored), optional
  sparkline. Used in the Overview KPI row.
- **Data table** — dense, sticky header, zebra-free with hover row tint, tabular-nums, sortable,
  color-coded P/L cells, truncation with expand. Horizontal scroll on mobile.
- **Equity line chart** — dual series, area-tint under the strategy line, crosshair tooltip,
  legend, "outperformance" callout.
- **Approval card** — the trade + a clear Approve (green) / Reject (red) pair, both confirmed.
- **Toggle switch / segmented control** — for mode, auto, enable, boolean settings.
- **Number/slider field** — for settings, with unit + min/max + helper.
- **Guarded action** (kill switch, mode→live, reject) — confirm dialog; kill switch is a
  distinct, always-reachable red control with an "engaged" loud state.
- **Pill/badge** — status (mode, market open), PoP bucket, IVR heat, source tag, win/loss.
- **Toast** — async action feedback (placed/closed/saved/error).
- **Empty / loading / error states** — skeletons for tables/cards; friendly empty copy
  ("No open positions", "Equity curve builds as the agent trades"); inline error with retry.
- **Live indicator** — small pulsing dot + "updated Ns ago".

---

## 7. Data & feature inventory (maps design → real API)

Base URL `http://localhost:8000`. The UI polls (SWR) ~every 8s.

| Endpoint | Returns / does | Screen |
|---|---|---|
| `GET /api/status` | `mode, kill_switch, market_open, starting_capital, requires_approval, scheduler_running` | Status bar |
| `GET /api/pnl` | `realized, unrealized, total, open_count, closed_count, wins, losses, win_rate, profit_pct, starting_capital` | Overview KPIs |
| `GET /api/benchmark` | `strategy_return_pct, sp500_return_pct, outperformance_pct, strategy_curve[], sp500_curve[]` | Equity chart |
| `GET /api/positions` | open trades (symbol, strategy, contracts, status, entry_credit, **probability_of_profit**, unrealized_pnl, dte_at_entry, rationale, legs[]) | Positions / Overview |
| `GET /api/trades/closed` | closed trades (+ realized_pnl, is_win, exit_reason) | Positions (Closed) |
| `GET /api/approvals` | pending-approval trades | Approval queue |
| `POST /api/approvals/{id}/approve` · `/reject` | act on a pending trade | Approval queue |
| `POST /api/cycle/run` | run one decision cycle now | Run-cycle button |
| `POST /api/scheduler/start` · `/stop` | start/stop the market-hours loop | Status bar / Settings |
| `POST /api/mode` · `POST /api/kill-switch` | set mode / engage kill switch | Status bar / Settings |
| `GET /api/watchlist` · `POST` · `DELETE /{symbol}` · `POST /{symbol}/toggle` · `POST /import` | watchlist CRUD | Watchlist |
| `GET /api/watchlist/ranked` | per-symbol IV rank / %ile / liquidity | Watchlist |
| `GET /api/tastytrade-watchlists` | tastytrade's public/recommended lists | Watchlist import |

**New endpoints the redesign needs (to build during implementation):**
- `GET /api/settings` + `PUT /api/settings` — read/update `StrategyParams` + `RiskLimits` +
  `working_capital` + scheduler config (so Settings is editable, not just viewable).
- `GET /api/activity` (or `/api/decisions`) — recent cycle decisions with commentary + outcomes
  for the Activity log.

---

## 8. Interaction & states

- **Real-time:** poll every ~8s; show a live dot + last-updated. Reserve space for async content
  (no layout jump).
- **Confirmations:** kill switch, switching to any live mode, reject, loosening a risk limit →
  confirm dialog (typed confirm for live mode).
- **Async buttons:** disable + spinner while running (Run cycle is ~30–60s).
- **Feedback:** toast on success/error for every mutating action.
- **Loading:** skeleton cards/rows. **Empty:** friendly copy. **Error:** inline message + retry.

---

## 9. Accessibility & responsive (hard requirements)

- Contrast ≥ 4.5:1 for all text (the palette above is tuned for this — verify gain/loss/red on
  `#0A0A0B`).
- Visible focus rings; full keyboard nav; tab order matches visual order.
- 44×44px min touch targets; `cursor: pointer` on all interactives.
- `aria-label` on icon-only buttons; `label` on every input; color is never the *only* signal
  (pair gain/loss color with `+`/`−` and an arrow).
- Responsive at **375 / 768 / 1024 / 1440**; no horizontal page scroll; 16px+ mobile inputs.
- `prefers-reduced-motion` respected.

---

## 10. Recommended implementation stack

The current app is **Next.js (App Router) + React 19 + TypeScript + SWR + Recharts** with plain
CSS. For the redesign, recommend adding:
- **Tailwind CSS** (theme tokens = the palette above) + **shadcn/ui** (accessible primitives:
  dialog, switch, tabs, tooltip, dropdown, toast, table) + **Lucide** icons. Keep **Recharts**
  for the equity chart. Keep **SWR** for polling.
- Define the palette as CSS variables / Tailwind theme tokens so brand red is one source of truth.

---

## 11. Screens to design (checklist)
- [ ] App shell: status bar + sidebar (desktop) and the mobile collapsed nav
- [ ] Overview: KPI row, equity chart, approval queue, open-positions snippet, recent activity
- [ ] Positions: Open + Closed tables with filters/sort
- [ ] Watchlist: ranked table + add + tastytrade import panel
- [ ] Activity / decision log feed
- [ ] Settings: Agent, Strategy, Management/Exits, Risk groups
- [ ] Dialogs: kill-switch confirm, mode→live confirm, reject confirm
- [ ] States: loading skeletons, empty states, error+retry, toasts
- [ ] Light note: there is **no** light mode requirement — dark only, on-brand.

---

### One-paragraph summary (for a design tool's first prompt)
> Redesign **TastyAgent**, a dark, data-dense AI options-trading control panel branded like
> tastytrade (black canvas `#0A0A0B`, white text, tastytrade red `#E4002B` for brand/CTAs/danger;
> green `#16C784` gains / red `#FF4D6A` losses). Build an app shell with a persistent top
> status bar (mode, market status, Auto toggle, total P/L, kill switch) and a left sidebar
> (Overview, Positions, Watchlist, Activity, Settings) + a pinned Run-cycle button. Inter for UI,
> JetBrains Mono for numbers, Lucide icons, 12px-radius cards. It must let the operator both
> *monitor* (P/L KPIs, equity-vs-S&P chart, positions with probability-of-profit, win/loss,
> approval queue, IV-rank watchlist, decision log) and *manage* (trading mode, kill switch,
> scheduler, working capital, strategy & risk settings, watchlist) with calm clarity and
> confirmed destructive actions. Fully accessible (4.5:1 contrast, focus rings, keyboard nav)
> and responsive (375/768/1024/1440).
