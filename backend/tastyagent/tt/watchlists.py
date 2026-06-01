"""Read tastytrade's public (curated/recommended) watchlists.

Lets the user browse the lists tastytrade publishes and import symbols into their
own watchlist. We keep only equity underlyings (skip futures `/…` and index `.…`
symbols the options agent can't trade).
"""

from __future__ import annotations

from tastytrade import Session
from tastytrade.watchlists import PublicWatchlist

_EQUITY_TYPES = {"Equity", "equity", None}


def _entry_symbol(entry) -> tuple[str | None, str | None]:
    if isinstance(entry, dict):
        return entry.get("symbol"), entry.get("instrument-type") or entry.get("instrument_type")
    return getattr(entry, "symbol", None), getattr(entry, "instrument_type", None)


# tastytrade's curated liquid-options universes, in priority order. The agent
# starts on these; the per-cycle ranking + guardrails pick the best each cycle.
SEED_LISTS = ("High Options Volume",)


async def seed_universe_from_tastytrade(repo, session: Session) -> int:
    """Seed an empty watchlist from tastytrade's recommended liquid lists.

    ``repo`` is duck-typed (needs ``.all()`` and ``.import_symbols``). Returns the
    number of symbols imported (0 if the watchlist already has entries).
    """
    if repo.all():
        return 0
    by_name = {w["name"]: w["symbols"] for w in await get_public_watchlists(session)}
    symbols: list[str] = []
    for name in SEED_LISTS:
        symbols.extend(by_name.get(name, []))
    if not symbols:
        return 0
    return repo.import_symbols(sorted(set(symbols)), "tt:High Options Volume")


async def get_public_watchlists(session: Session) -> list[dict]:
    """Return [{name, group, symbols}] for tastytrade's public watchlists."""
    watchlists = await PublicWatchlist.get(session)
    out: list[dict] = []
    for wl in watchlists:
        symbols: list[str] = []
        for entry in wl.watchlist_entries or []:
            sym, itype = _entry_symbol(entry)
            # skip futures (/…), index (.…), and indicator ($…) symbols
            if not sym or sym[0] in "/.$":
                continue
            if itype not in _EQUITY_TYPES:
                continue
            symbols.append(sym.upper())
        if symbols:
            out.append(
                {"name": wl.name, "group": wl.group_name, "symbols": sorted(set(symbols))}
            )
    return out
