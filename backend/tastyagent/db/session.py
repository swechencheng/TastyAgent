"""Engine + session factory. Defaults to a SQLite file; supports in-memory for tests."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

DEFAULT_DB_PATH = (
    Path(__file__).resolve().parent.parent.parent / "data" / "tastyagent.db"
)


def make_engine(url: str | None = None, *, echo: bool = False) -> Engine:
    if url is None:
        DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        url = f"sqlite:///{DEFAULT_DB_PATH}"
    return create_engine(url, echo=echo, future=True)


def init_db(engine: Engine) -> None:
    Base.metadata.create_all(engine)
    with engine.connect() as conn:
        try:
            from sqlalchemy import text

            res = conn.execute(text("PRAGMA table_info(trades)"))
            cols = {row[1] for row in res.fetchall()}
            if cols:
                if "tp_order_id" not in cols:
                    conn.execute(text("ALTER TABLE trades ADD COLUMN tp_order_id TEXT"))
                if "order_ref" not in cols:
                    conn.execute(text("ALTER TABLE trades ADD COLUMN order_ref TEXT"))
                conn.commit()
        except Exception:
            pass


def session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


def in_memory_session() -> Session:
    """A ready-to-use session backed by a fresh in-memory DB (tests/dev)."""
    engine = make_engine("sqlite:///:memory:")
    init_db(engine)
    return session_factory(engine)()
