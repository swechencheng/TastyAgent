# Fonts

IBTastyAgent uses two typefaces, both **free and open-source on Google Fonts**:

| Role                    | Family             | Weights used       | Notes                                                                          |
| ----------------------- | ------------------ | ------------------ | ------------------------------------------------------------------------------ |
| UI / headings / body    | **Inter**          | 400, 500, 600, 700 | Clean, neutral, financial. The brief also allows Geist Sans as an alternative. |
| Numbers / tables / code | **JetBrains Mono** | 400, 500, 600, 700 | Tabular figures so prices, P/L, deltas and percentages align in columns.       |

## How they're loaded

`colors_and_type.css` imports both from the Google Fonts CDN:

```css
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap");
```

The UI kit and preview cards link the same Google Fonts stylesheet in their `<head>`.

## ⚠️ Substitution flag

The IBTastyAgent repo ships **no font files** — it relied on system/CDN fonts. We are
therefore loading Inter + JetBrains Mono **from the Google Fonts CDN** rather than from
local `.ttf`/`.woff2` files in this folder.

**If you want self-hosted/offline fonts**, drop the `.woff2` files into this folder and
swap the `@import` for `@font-face` rules. Both families are available at
<https://fonts.google.com/specimen/Inter> and
<https://fonts.google.com/specimen/JetBrains+Mono>.

Always use `font-variant-numeric: tabular-nums` (or JetBrains Mono) for any numeric
column so figures stay aligned.
