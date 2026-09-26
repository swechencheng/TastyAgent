from datetime import date
import pytest

from tastyagent.db.models import Trade, TradeLeg, TradeStatus
from tastyagent.db.session import in_memory_session, init_db
from tastyagent.execution.exit_manager import audit_take_profit_orders
from tastyagent.portfolio.ledger import Ledger


@pytest.fixture
def ledger():
    s = in_memory_session()
    init_db(s.bind)
    return Ledger(s)


async def test_audit_take_profit_detects_missing_order(ledger):
    trade = Trade(
        symbol="SPY",
        strategy="short_strangle",
        contracts=1,
        status=TradeStatus.OPEN,
        mode="sandbox",
        entry_credit=200.0,
        broker_order_id="1001",
        tp_order_id=None,  # No TP attached!
        legs=[
            TradeLeg(
                option_type="put",
                strike=550.0,
                expiration=date(2026, 11, 20),
                action="sell_to_open",
                quantity=1,
            ),
            TradeLeg(
                option_type="call",
                strike=600.0,
                expiration=date(2026, 11, 20),
                action="sell_to_open",
                quantity=1,
            ),
        ],
    )
    ledger.s.add(trade)
    ledger.s.commit()

    active_order_ids = {"1001"}  # Only entry order, no TP order
    alerts = await audit_take_profit_orders(ledger, active_order_ids)

    assert len(alerts) == 1
    assert "has NO active Take-Profit order" in alerts[0]
    assert "SPY" in alerts[0]


async def test_audit_take_profit_happy_path_when_active(ledger):
    trade = Trade(
        symbol="QQQ",
        strategy="short_strangle",
        contracts=1,
        status=TradeStatus.OPEN,
        mode="sandbox",
        entry_credit=200.0,
        broker_order_id="2001",
        tp_order_id="2002",  # TP active!
        legs=[],
    )
    ledger.s.add(trade)
    ledger.s.commit()

    active_order_ids = {"2001", "2002"}
    alerts = await audit_take_profit_orders(ledger, active_order_ids)

    assert len(alerts) == 0  # No alert triggered


async def test_audit_take_profit_auto_attaches(ledger):
    trade = Trade(
        symbol="TSLA",
        strategy="iron_condor",
        contracts=1,
        status=TradeStatus.OPEN,
        mode="sandbox",
        entry_credit=300.0,
        broker_order_id="3001",
        tp_order_id=None,
        legs=[],
    )
    ledger.s.add(trade)
    ledger.s.commit()

    async def mock_attach(t):
        return "3002"

    alerts = await audit_take_profit_orders(
        ledger, active_broker_order_ids=set(), auto_attach_fn=mock_attach
    )
    assert len(alerts) == 1
    assert trade.tp_order_id == "3002"
