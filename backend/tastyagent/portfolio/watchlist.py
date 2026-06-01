"""The trading-universe watchlist: persistent, user-editable, importable.

The agent analyzes the *enabled* symbols here. Seeded from the curated default the
first time it's read so the agent works out of the box; the user then edits it from
the dashboard or imports tastytrade's public (recommended) watchlists.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import WatchlistEntry


def _norm(symbol: str) -> str:
    return symbol.strip().upper()


class WatchlistRepo:
    def __init__(self, session: Session) -> None:
        self.s = session

    def all(self) -> list[WatchlistEntry]:
        return list(self.s.scalars(select(WatchlistEntry).order_by(WatchlistEntry.symbol)))

    def symbols(self) -> list[str]:
        """Enabled symbols — the agent's trading universe."""
        return [e.symbol for e in self.all() if e.enabled]

    def seed_default_if_empty(self, default_symbols: list[str]) -> None:
        if self.s.scalar(select(WatchlistEntry).limit(1)) is None:
            for sym in default_symbols:
                self.s.add(WatchlistEntry(symbol=_norm(sym), source="default"))
            self.s.commit()

    def add(self, symbol: str, source: str = "custom") -> WatchlistEntry:
        sym = _norm(symbol)
        entry = self.s.get(WatchlistEntry, sym)
        if entry is None:
            entry = WatchlistEntry(symbol=sym, source=source, enabled=True)
            self.s.add(entry)
        else:
            entry.enabled = True  # re-adding re-enables
        self.s.commit()
        return entry

    def import_symbols(self, symbols: list[str], source: str) -> int:
        added = 0
        for sym in symbols:
            sym = _norm(sym)
            if not sym:
                continue
            if self.s.get(WatchlistEntry, sym) is None:
                self.s.add(WatchlistEntry(symbol=sym, source=source))
                added += 1
        self.s.commit()
        return added

    def remove(self, symbol: str) -> bool:
        entry = self.s.get(WatchlistEntry, _norm(symbol))
        if entry is None:
            return False
        self.s.delete(entry)
        self.s.commit()
        return True

    def set_enabled(self, symbol: str, enabled: bool) -> WatchlistEntry | None:
        entry = self.s.get(WatchlistEntry, _norm(symbol))
        if entry is None:
            return None
        entry.enabled = enabled
        self.s.commit()
        return entry
