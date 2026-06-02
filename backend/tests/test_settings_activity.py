from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from tastyagent.api.app import create_app
from tastyagent.api.runtime import Runtime
from tastyagent.config import TradingMode
from tastyagent.db.session import init_db
from tastyagent.portfolio.ledger import Ledger

from .conftest import make_candidate


def factory():
    eng = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool, future=True
    )
    init_db(eng)
    return sessionmaker(bind=eng, expire_on_commit=False, future=True)


def client(sf=None):
    return TestClient(create_app(sf or factory(), Runtime(mode=TradingMode.SANDBOX)))


def test_settings_get_shape():
    j = client().get("/api/settings").json()
    assert j["mode"] == "sandbox"
    assert j["working_capital"] == 10000.0
    assert "min_iv_rank" in j["strategy"] and "universe_top_n" in j["strategy"]
    assert "max_trade_bp_pct" in j["risk"]
    assert "kill_switch" not in j["risk"]  # kill switch is its own toggle
    assert j["scheduler"]["market_hours_only"] is True


def test_settings_put_partial_update():
    c = client()
    r = c.put(
        "/api/settings",
        json={
            "working_capital": 25000,
            "scheduler_interval_seconds": 120,
            "strategy": {"min_iv_rank": 0.4, "universe_top_n": 20, "bogus": 1},
            "risk": {"max_trade_bp_pct": 0.08, "kill_switch": True},
        },
    ).json()
    assert r["working_capital"] == 25000
    assert r["scheduler"]["interval_seconds"] == 120
    assert r["strategy"]["min_iv_rank"] == 0.4
    assert r["strategy"]["universe_top_n"] == 20  # coerced to int
    assert "bogus" not in r["strategy"]  # unknown key ignored
    assert r["risk"]["max_trade_bp_pct"] == 0.08
    # persisted on the runtime
    assert c.get("/api/settings").json()["strategy"]["min_iv_rank"] == 0.4


def test_settings_put_rejects_bad_capital():
    assert client().put("/api/settings", json={"working_capital": 0}).status_code == 400


def test_activity_feed():
    sf = factory()
    lg = Ledger(sf())
    d = lg.record_decision(TradingMode.SANDBOX, "sold a strangle in XLE", 3)
    lg.record_planned(make_candidate(symbol="XLE"), 1, "high IVR", TradingMode.SANDBOX, d)
    lg.record_rejected(make_candidate(symbol="SPY"), "risk: too big", TradingMode.SANDBOX, d)

    items = client(sf).get("/api/activity").json()
    assert len(items) == 1
    a = items[0]
    assert a["commentary"] == "sold a strangle in XLE"
    assert a["considered"] == 3
    assert a["placed"] == 1
    assert a["rejected"] == 1
    assert a["symbols"] == ["XLE"]
