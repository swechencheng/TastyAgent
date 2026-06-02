---
name: tastyagent-design
description: Use this skill to generate well-branded interfaces and assets for TastyAgent, either for production or throwaway prototypes/mocks/etc. Contains essential design guidelines, colors, type, fonts, assets, and UI kit components for prototyping.
user-invocable: true
---

Read the `README.md` file within this skill, and explore the other available files.

If creating visual artifacts (slides, mocks, throwaway prototypes, etc), copy assets out and
create static HTML files for the user to view. If working on production code, you can copy
assets and read the rules here to become an expert in designing with this brand.

If the user invokes this skill without any other guidance, ask them what they want to build or
design, ask some questions, and act as an expert designer who outputs HTML artifacts _or_
production code, depending on the need.

## What's here
- `README.md` — product context, CONTENT FUNDAMENTALS, VISUAL FOUNDATIONS, ICONOGRAPHY, and a
  file index. Start here.
- `colors_and_type.css` — the token layer (color + type CSS vars and semantic classes). Import
  this first in any TastyAgent artifact.
- `fonts/` — Inter + JetBrains Mono (Google Fonts) setup + self-hosting note.
- `assets/` — the TastyAgent wordmark SVG.
- `preview/` — small reference cards for colors, type, spacing, components, brand.
- `ui_kits/dashboard/` — a high-fidelity, interactive recreation of the control panel
  (status bar, sidebar, Overview/Positions/Watchlist/Activity/Settings, dialogs, toasts).
  Lift components from here; mock data + API shapes are in `components.jsx`.
- `_source/frontend/` — reference code imported from `github.com/brandons17563/TastyAgent`.

## Non-negotiables (the brand in one breath)
- Dark only. Near-black canvas `#0A0A0B`, pure-black chrome, white text, **tastytrade red
  `#E4002B`**. Red **fills = actions/danger**; red **text = negative P/L** (use the brighter
  `#FF4D6A`). Gains `#16C784`.
- **Inter** for UI, **JetBrains Mono + tabular-nums** for all numbers.
- **Lucide** icons only (20–24px, 1.5px stroke). No emoji.
- 12px cards · 8px inputs · 999px pills. Flat elevation (surface color + 1px border + faint top
  sheen), no heavy shadows. Calm 150–250ms motion. ≥4.5:1 contrast, visible focus rings.
- Voice: calm trading-desk, second person, plain-English "why", confirmed destructive actions.
  `tastytrade` always lowercase.

> Educational / paper-trading framing — keep risk and destructive actions explicit. Not
> financial advice.
