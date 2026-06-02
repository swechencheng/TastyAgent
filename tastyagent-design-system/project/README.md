# TastyAgent — Design System

A design system for **TastyAgent**, an AI options-trading agent that trades tastytrade's
premium-selling methodology. Deterministic tastytrade mechanics act as **hard guardrails**;
Claude provides an **adaptive selection layer within those rails**. It paper-trades through
tastytrade's sandbox, manages winners and defends/rolls losers, and surfaces everything on a
live dashboard with P/L vs. the S&P 500.

This system captures the brand, foundations, components, and a high-fidelity UI kit so any
agent or designer can produce on-brand TastyAgent interfaces and assets.

---

## Product context

- **What it is:** a single-operator AI trading agent + a **data-dense financial control
  panel** to monitor and manage it. Think Bloomberg/trading-terminal clarity — *not* playful
  SaaS. Calm by default; loud only when something needs attention (a loss, a pending approval,
  the kill switch).
- **The user:** one trader running their own agent. They **monitor** it (is it making money,
  what's open, what did it decide and why) and **manage** it (mode, risk, strategy, watchlist,
  kill switch), often glancing at it during the trading day.
- **The surface:** one cohesive responsive web app — a persistent top **status bar** + left
  **sidebar** (Overview · Positions · Watchlist · Activity · Settings) + a pinned **Run cycle**
  button. Dark only, on-brand. No mobile-native app, no charting/TA tooling, no backtesting.

### Sources used to build this system

> The reader may not have access to these; they are recorded so the system can be regenerated
> or deepened. **Explore these repositories to build richer, more accurate TastyAgent
> designs.**

- **GitHub repo:** `brandons17563/TastyAgent` — <https://github.com/brandons17563/TastyAgent>
  - `docs/UI_REDESIGN_BRIEF.md` — the authoritative redesign brief (brand, IA, every screen,
    every data field mapped to the API, component patterns). **This is the design authority
    for the system** and the primary source for everything here.
  - `frontend/` — the current Next.js dashboard (React 19 + TS + SWR + Recharts). Imported to
    `_source/frontend/` for reference — it gave us the real data shapes and the
    monitor-screen logic. Note: the live code is the *pre-redesign* layout; this system targets
    the **redesign** described in the brief.
  - `README.md` — the methodology (guardrails, strategies, exits/defense, modes & safety).

The TastyAgent repo ships **no logo or font files** — the brand mark is a text wordmark and
fonts are open-source (see *Visual foundations* and `fonts/`).

---

## CONTENT FUNDAMENTALS

How TastyAgent writes. The voice is a **calm, precise trading desk** — plain-English, second
person, never hypey.

- **Voice & person:** speaks **to the operator** as "you" / imperative ("Run cycle", "Add
  ticker", "Approve"). Refers to the system as "the agent" or "TastyAgent" (third person), and
  attributes reasoning to **"Claude"** ("Claude's commentary", "Claude selects & sizes").
- **Tone:** factual, confident, understated. It explains the *why* in one plain sentence —
  e.g. *"IV rank 82 — elevated. 16Δ short strikes, liquid chain, no earnings in window. Sized
  to 4% BP."* No exclamation marks, no persuasion, no "🚀 to the moon."
- **Casing:**
  - Page titles and nav: **Title case** ("Overview", "Watchlist", "Run cycle").
  - Section labels inside panels: **UPPERCASE, tracked** ("OPEN POSITIONS", "NEEDS ATTENTION").
  - Buttons: sentence/Title case ("Run cycle", "Browse tastytrade lists", "Save changes").
  - **`tastytrade` is always lowercase** (brand styling); "tastytrade red", "tt:High Options
    Volume".
  - Trading modes are lowercase tokens: `sandbox`, `live_approval`, `live_auto`.
- **Numbers:** money as `+$420.18` / `−$112.40` (explicit sign, 2 decimals, minus sign `−`
  not hyphen for losses). Percentages `+4.20%`, `68%`. Deltas always carry a sign **and** an
  arrow (`▲ 4.20%`) so color is never the only signal.
- **Domain vocabulary (use precisely):** IV rank / IVR, DTE (days to expiration), PoP
  (probability of profit), BP (buying power), credit, short strangle, naked put, put/call
  credit spread, iron condor, roll out, roll the untested side, take-profit, ahead-of-pace,
  kill switch, working capital, universe / watchlist, cycle.
- **Safety language:** destructive/risky actions are spelled out and confirmed — *"Halts ALL
  new entries instantly."* / *"This trades a real account. Type LIVE to confirm."* Honest about
  limits ("PoP is a delta-based estimate", "sandbox fills are unreliable").
- **Emoji:** **none** in the product UI. (The source README uses ⚠️ for a disclaimer callout in
  Markdown only — never in the app.)
- **Empty/loading/error copy:** friendly and literal — *"No open positions."*, *"Equity curve
  builds as the agent trades."*, inline error + **retry**.

---

## VISUAL FOUNDATIONS

**Theme:** dark, tastytrade **black / white / red**. Dark only — there is no light mode.

### Color
- **Canvas is near-black** `#0A0A0B`; the deepest chrome (status bar, sidebar) is **pure black**
  `#000`. Content sits on raised **surfaces** by *color*, not shadow: `surface #141417` for
  cards, `surface-2 #1C1C21` for inputs / nested rows / hover fills, hairline `border #2A2A30`.
- **Brand = tastytrade red `#E4002B`** (`brand-hover #FF1F47`, `brand-press #C20025`). Used for
  the logo, primary CTA fills, active nav, and danger fills.
- **The key disambiguation rule:** red **fills = actions/danger**; red **text = negative
  values**. Negative P/L text uses a *brighter* `#FF4D6A` (4.5:1 on black); gains are
  `#16C784`. Soft 13%-alpha tints (`#16C78422` / `#FF4D6A22`) back chips and the equity area.
- **Status:** `warn #F0A500` (near-DTE, approval pending), `info #4C9AFF` (neutral links, used
  sparingly — red stays the hero accent).
- **Text ramp:** `#FFFFFF` primary → `#9A9AA4` muted → `#6B6B74` faint. Every text/bg pair
  meets **≥ 4.5:1**.
- *Note:* the brief specifies `#E4002B` and flags verifying against the live tastytrade brand;
  third-party brand databases list a darker `#720F12` and a green. **We follow the brief** —
  vivid `#E4002B` is the system's single source of truth for brand red.

### Type
- **Inter** for all UI / headings / body (weights 400–700). Geist Sans is an allowed alt.
- **JetBrains Mono** for **all numbers** — prices, P/L, deltas, %, DTE, IVR — with
  `font-variant-numeric: tabular-nums` so figures align in columns.
- Scale: KPI numbers 28–34px · page title 20–24px · UPPERCASE section labels 15px · body 14px ·
  tables 13–14px · tags 11px. Line-height 1.5 for prose, ~1.2 for numbers. Min 16px mobile
  inputs.

### Shape, spacing, elevation
- **Radii:** 12px cards, 8px inputs/buttons, 999px pills.
- **Spacing:** 4px base scale (4 · 8 · 12 · 16 · 20 · 24 · 32 · 40).
- **Elevation is flat:** surface color + a 1px border + a barely-there top sheen
  (`inset 0 1px 0 rgba(255,255,255,0.03)`). **Avoid heavy shadows on black.** The only real
  shadow is on floating layers (dialogs, menus, toasts): `0 8px 24px rgba(0,0,0,.5)`.
- **Cards:** `#141417` fill, 1px `#2A2A30` border, 12px radius, 16–18px padding, the inset
  sheen. No drop shadow, no colored left-border accents — *except* the deliberate semantic
  accents: a **warn** left-border on approval cards, a **brand** left-border on the kill banner.

### Backgrounds, imagery, texture
- **No imagery, no illustrations, no photography, no gradients-as-decoration.** The product is
  flat fields of near-black + hairlines. The only "gradient" is the soft brand/gain/loss tint
  fills behind chips and under the equity line. The equity chart is a clean dual-line SVG
  (brand-red strategy line + muted-grey S&P), area-tinted in `brand-soft`.

### Motion
- **Calm and quick:** 150–250ms transitions on **color / opacity / transform only**. Toggles
  slide 200ms; toasts rise-and-fade; the active "live" / "Auto ON" state shows a small
  **pulsing dot** (the one piece of perpetual motion). Honor `prefers-reduced-motion`.

### Interaction states
- **Hover:** buttons lighten (primary → `brand-hover`); secondary/ghost controls brighten their
  border to `border-strong`; table rows tint to `surface-2`; nav items go from muted to white.
- **Press:** subtle `transform: scale(.97)` on buttons.
- **Focus:** a visible 2px brand ring offset from the canvas (`0 0 0 2px bg, 0 0 0 4px brand`).
- **Disabled:** drop to `surface-2` fill + `text-faint`, no pointer.
- **Toggles** turn **green** (`gain`) when on; **Auto** and **live** dots pulse green; the
  **kill switch** is a red-outline ghost that becomes a solid-red "engaged" state.

### Transparency & blur
- Used **only** for overlays: the dialog scrim is `rgba(0,0,0,.6)` with a light `blur(2px)`.
  Chips/tints use 13% alpha. Otherwise surfaces are opaque.

### Layout rules
- **Fixed chrome:** the status bar (56px, pure black) and the sidebar (220px, pure black) are
  persistent; only the content area scrolls. A **Run cycle** primary button is pinned to the
  sidebar bottom. Content max-width ~1080px, generous 28–32px padding.
- **Responsive:** sidebar collapses to a bottom tab bar under 680px; KPI grid drops to 2-up
  under 920px; tables scroll horizontally. Breakpoints tuned at 375 / 768 / 1024 / 1440.

---

## ICONOGRAPHY

- **Library:** **Lucide** SVG icons, **only**. 20–24px, **1.5px stroke**, `currentColor`.
  No emoji, no unicode glyphs-as-icons, no icon font, no PNG icons. (Small geometric marks like
  the `▲`/`▼` P/L arrows and the live `●` dot are intentional typographic accents, not icons.)
- **Delivery:** linked from the Lucide CDN
  (`https://unpkg.com/lucide@0.460.0/dist/umd/lucide.min.js`) and rendered via
  `data-lucide="<name>"` + `lucide.createIcons()`. The source repo had **no icon assets** of
  its own, so Lucide is the system standard (per the brief) — *not* a substitution.
- **Core set in use:** `layout-dashboard` (Overview), `layers` (Positions), `list-checks`
  (Watchlist), `activity` (Activity), `settings` (Settings), `play` / `loader` (Run cycle),
  `octagon-x` (kill switch), `bot` (mode/agent), `bell` (needs attention), `shield` (risk),
  `target` (strategy), `hand-coins` (management/exits), `trending-up` / `trending-down`,
  `check` / `x`, `flame` (IV rank), `clock` (DTE), `plus` / `list-plus` (add/import),
  `trash-2`, `chevron-down/up`, `arrow-right`, `triangle-alert` / `info` (dialogs),
  `circle-check` / `circle-x` (toasts).
- **Logo / brand mark:** a **text wordmark** — `Tasty` in white + `Agent` in brand red, Inter
  700, tight tracking. There is no separate symbol/glyph. See `assets/logo-wordmark.svg` and
  the `preview/brand-wordmark.html` card. On a red field, the whole wordmark goes white.

---

## File index (manifest)

Root:
- **`README.md`** — this file: product context, content & visual foundations, iconography, index.
- **`colors_and_type.css`** — the token layer: color CSS vars + semantic type vars/classes.
  Import this first in any TastyAgent artifact.
- **`SKILL.md`** — Agent-Skills-compatible entry point for using this system.
- **`fonts/`** — `README.md` documenting the Inter + JetBrains Mono (Google Fonts) setup and
  the self-hosting swap note.
- **`assets/`** — `logo-wordmark.svg` (the TastyAgent wordmark).
- **`preview/`** — 19 small Design-System cards (Colors, Type, Spacing, Components, Brand) that
  populate the Design System tab.
- **`_source/frontend/`** — imported reference code from the repo (data shapes + current
  screens). Reference only; not part of the deliverable.

UI kits:
- **`ui_kits/dashboard/`** — the high-fidelity, interactive recreation of the TastyAgent
  control panel (status bar, sidebar, Overview, Positions, Watchlist, Activity, Settings,
  dialogs, toasts). See its own `README.md`. Open `index.html` to use it.

---

> ⚠️ **Educational project. Not financial advice.** TastyAgent is a paper-trading demo; this
> design system inherits that framing. Risk/destructive actions in any TastyAgent design must
> stay explicit and confirmed.
