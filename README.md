# TastyAgent

An AI options-trading agent that trades **tastytrade's premium-selling methodology**. Deterministic
tastytrade mechanics act as hard guardrails; an OpenRouter LLM provides an adaptive selection layer *within*
those rails. It paper-trades through tastytrade's sandbox, manages winners and defends/rolls losers,
and surfaces everything on a live dashboard with P/L vs. the S&P 500.

> ⚠️ **Educational project. Not financial advice.** Options trading involves substantial risk. Run it
> in the sandbox. Only point it at real money once you fully understand it and accept the risk.

---

## How it works

```
market context (IV rank / regime)
        │
        ▼
generate candidates ─ strangles · naked puts · put/call credit spreads · iron condors
        │             (real option chains + streamed greeks)
        ▼
HARD GUARDRAILS  ── IV rank · ~45 DTE · ~16Δ strikes · liquidity · earnings · BP caps
        │
        ▼
LLM selects & sizes (OpenRouter)  ── adaptive layer, within the rails, writes a plain-English rationale
        │
        ▼
POST-LLM RE-VALIDATION  ── guardrails + sizing + portfolio risk recomputed (LLM can't bypass them)
        │
        ▼
execute  ── sandbox auto · live = one-click approval queue
        │
        ▼
manage every cycle  ── take profit (50% / ahead-of-pace schedule) · roll out at 21 DTE ·
                       roll the untested side when tested · (optional hard stop)
```

The **adaptive (LLM) layer is deliberately fenced in**: every trade it picks is re-validated against
the deterministic guardrails, sizing, and portfolio-risk limits before anything is placed.

---

## Prerequisites

- **Python 3.11+** and **Node.js 20+**
- A **tastytrade account** with API access, and:
  - a **sandbox (cert) OAuth grant** with `read trade` scope (for paper trading)
  - a **production read-only OAuth grant** (`read` scope only) — used *only* to fetch IV rank, which
    the sandbox doesn't serve. Read-only means it physically cannot place a live order.
- An **OpenRouter API key** (for the adaptive selection layer, default model: `deepseek/deepseek-v4.1-flash`)

> Paths below use Windows (`​.venv\Scripts\…`). On macOS/Linux use `.venv/bin/…`.

---

## Setup

### 1. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"     # installs the package + test deps
copy .env.example .env                                # then fill it in (next step)
```

### 2. Credentials (`backend/.env`)

`.env` is gitignored — never commit it. Fill in:

| Variable | What it is |
|---|---|
| `TASTYAGENT_MODE` | `sandbox` (default), `live_approval`, or `live_auto` |
| `TASTYTRADE_USERNAME` / `TASTYTRADE_PASSWORD` | your sandbox user (used once to provision/fund the paper account) |
| `TASTYTRADE_ACCOUNT` | sandbox account number (set after provisioning) |
| `TASTYTRADE_CLIENT_SECRET` / `TASTYTRADE_OAUTH_REFRESH_TOKEN` | sandbox `read trade` OAuth grant |
| `TASTYTRADE_PROD_CLIENT_SECRET` / `TASTYTRADE_PROD_OAUTH_REFRESH_TOKEN` | **production read-only** grant (IV rank) |
| `OPENROUTER_API_KEY` | OpenRouter API key |
| `OPENROUTER_MODEL` | defaults to `deepseek/deepseek-v4.1-flash` |
| `OPENROUTER_BASE_URL` | optional, defaults to `https://openrouter.ai/api/v1` |
| `TASTYAGENT_WORKING_CAPITAL` | capital the agent sizes against (default **$10,000**) |

Create OAuth grants at `my.tastytrade.com → Manage → My Profile → API → OAuth Applications`
(2FA must be enabled for the `read`/`trade` scopes). The sandbox grant is issued in the cert
environment; the prod read-only grant is a separate app with `read` scope only.

### 3. Provision & fund the sandbox account

The sandbox wipes balances every 24h, so re-run this whenever you start a session:

```bash
cd backend
.venv\Scripts\python scripts\provision_sandbox.py     # creates (if needed) + funds the paper account to $1M
```

### 4. Frontend

```bash
cd frontend
npm install
# optional: set NEXT_PUBLIC_API_BASE if the API isn't on http://localhost:8000
```

---

## Running it

Two terminals:

```bash
# Terminal 1 — API
cd backend
.venv\Scripts\python -m uvicorn tastyagent.api.app:app --port 8000

# Terminal 2 — dashboard
cd frontend
npm run dev            # http://localhost:3000
```

From the **dashboard** you can:
- **Run cycle** — run one full decision cycle now (gather context → generate candidates → LLM
  selects → re-validate → place)
- **Auto: ON/OFF** — start/stop the market-hours scheduler loop
- **Mode** switch and **Kill switch** (halts all new entries instantly)
- Edit the **watchlist** (the agent's universe) — add/remove/disable tickers, **browse and import
  tastytrade's recommended lists** (e.g. "High Options Volume"), and see live **IV rank** per symbol
- Watch open positions (with rationale + **probability of profit**), win/loss lists, P/L cards, the
  pending-approval queue (live mode), and the **equity curve vs. S&P 500**

Or drive a single cycle from the CLI:

```bash
cd backend
.venv\Scripts\python scripts\run_cycle.py
```

---

## Trading modes & safety

| Mode | Behavior |
|---|---|
| `sandbox` | Paper trading on tastytrade cert. Places automatically. The liquidity-width guardrail is relaxed (cert quotes are delayed/wide). |
| `live_approval` | Real account. **Every order waits in the dashboard approval queue** until you click Approve. |
| `live_auto` | Real account, fully autonomous (opt-in). |

Safety rails (all in `backend/tastyagent/config.py`): per-trade & total buying-power caps, max
positions, per-symbol concentration, daily-loss halt, consecutive-loss halt, and a hard **kill
switch**. The LLM cannot bypass any of them — they're re-checked after it selects.

---

## The methodology (encoded as guardrails)

- **Universe:** on first run the watchlist is **seeded from tastytrade's "High Options Volume" list**
  (~194 liquid optionable names, fetched live). You then edit it freely or import other recommended
  lists. Each cycle the agent batches one IV-rank call across the whole universe and does the
  expensive chain/greeks work only on the **top-N highest-IVR liquid names** (`universe_top_n`), so a
  big watchlist stays fast.
- **Entry:** sell premium when **IV rank** is elevated; ~**45 DTE**; ~**16-delta** short strikes;
  liquidity + earnings filters; small buying-power allocation per trade.
- **Strategies:** short strangle, naked put, put/call credit spreads, iron condor (the LLM chooses by
  IV rank, account size, and buying power; defined-risk preferred when BP is constrained).
- **Manage winners:** take profit at 50% of max, **or earlier on an "ahead-of-pace" schedule**
  (per-strategy days-held-to-profit table) — close a winner the moment it reaches a milestone faster
  than average.
- **Defend losers:** **roll out** to the next cycle at 21 DTE; **roll the untested side** in for a
  credit when a short leg gets tested. Hard stop-loss is **off by default** (tastytrade manages, not
  stops).
- **Probability of profit** is shown per trade (delta-based estimate; a 16Δ strangle ≈ ~68%).

---

## Tests

```bash
cd backend
.venv\Scripts\python -m pytest -q       # 90 deterministic tests, no network
```

The safety-critical core (guardrails, sizing, exits/defense, risk limits, ledger, executor,
candidate builders, API) is fully unit-tested.

## Helper scripts (`backend/scripts/`)

| Script | Purpose |
|---|---|
| `provision_sandbox.py` | create + fund the sandbox paper account (idempotent; re-run after the daily reset) |
| `check_sandbox.py` | verify sandbox OAuth login, list accounts/balances/positions |
| `check_metrics.py` | verify IV rank via the production read-only grant |
| `check_candidates.py` | live market context + candidate generation for a small watchlist |
| `check_llm.py` | verify OpenRouter LLM structured selection |
| `run_cycle.py` | run one full decision cycle against the sandbox |
| `reset.py` | clean slate — cancel all live sandbox orders + wipe the local ledger |

---

## Project layout

```
backend/tastyagent/
  config.py · settings.py · models.py          # config, env, domain types (+ PoP)
  strategy/   guardrails · sizing · exits · profit_schedule · candidates
  risk/       limits                           # portfolio safety rails
  tt/         client · ratelimit · marketdata · metrics · orders   # tastytrade API
  decision/   context · llm · orchestrator     # market context + OpenRouter LLM + pipeline
  execution/  executor · sandbox_placer · exit_manager · tracker
  portfolio/  ledger · pnl · benchmark         # source-of-truth ledger, P/L, S&P
  db/         models · session                 # SQLite via SQLAlchemy
  runner.py · scheduler.py · api/              # the cycle tick, loop, FastAPI app
frontend/                                       # Next.js dashboard
```

---

## Known limitations (honest)

- **Sandbox fills are unreliable** — cert limit orders often sit `working` and rarely fill to `open`,
  so realized P/L and live exit/roll *execution* are hard to demo there (the logic is unit-tested and
  runs in production). Quotes are 15-min delayed.
- **IV rank is production-only** — sandbox doesn't serve `/market-metrics`, hence the separate
  read-only prod grant.
- **No backtesting (by design)** — TastyAgent trades tastytrade's already-researched strategies
  rather than inventing its own, so **sandbox paper trading is the validation method**.
- **Working capital is simulated** — the sandbox seeds ~$1M with no withdrawal endpoint, so the agent
  sizes against `TASTYAGENT_WORKING_CAPITAL` ($10k default), not the broker's balance. At $10k the
  agent favors small defined-risk spreads (SPY strangles need ~$15k BP, so they're correctly out of
  reach).
- **PoP is a delta-based estimate**, not a full pricing-model probability.
```
