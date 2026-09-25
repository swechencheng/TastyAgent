from types import SimpleNamespace
import pytest

from ib_async import Option
from tastyagent.ibkr.orders import (
    build_closing_tp_order,
    build_combo_contract,
    build_manual_close_order,
    build_opening_credit_order,
)


def test_build_combo_contract():
    opt1 = Option("TSLA", "20261120", 350.0, "P", "SMART", conId=101)
    opt2 = Option("TSLA", "20261120", 400.0, "C", "SMART", conId=102)

    combo = build_combo_contract("TSLA", [(opt1, "SELL"), (opt2, "SELL")])
    assert combo.secType == "BAG"
    assert combo.symbol == "TSLA"
    assert len(combo.comboLegs) == 2
    assert combo.comboLegs[0].conId == 101
    assert combo.comboLegs[0].action == "SELL"
    assert combo.comboLegs[1].conId == 102
    assert combo.comboLegs[1].action == "SELL"


def test_build_opening_credit_order():
    order = build_opening_credit_order(
        contracts=2,
        credit_per_share=1.50,
        account="U123456",
        order_ref="TastyAgent_1",
    )
    assert order.action == "BUY"  # Buying credit combo
    assert order.lmtPrice == -1.50  # Negative price = net credit in IBKR
    assert order.totalQuantity == 2
    assert order.account == "U123456"
    assert order.orderRef == "TastyAgent_1"
    assert order.overridePercentageConstraints is True


def test_build_closing_tp_order():
    order = build_closing_tp_order(
        contracts=2,
        tp_debit_per_share=0.75,
        account="U123456",
        order_ref="TastyAgent_TP_1",
        parent_id=5001,
    )
    assert order.action == "SELL"  # Selling to close credit combo
    assert order.lmtPrice == -0.75  # Negative price = net debit paid to close
    assert order.totalQuantity == 2
    assert order.tif == "GTC"
    assert order.parentId == 5001
    assert order.orderRef == "TastyAgent_TP_1"
    assert order.overridePercentageConstraints is True


def test_build_manual_close_order():
    order = build_manual_close_order(
        contracts=1,
        debit_per_share=2.10,
        account="U123456",
        order_ref="TastyAgent_CLOSE_1",
    )
    assert order.action == "SELL"
    assert order.lmtPrice == -2.10
    assert order.totalQuantity == 1
    assert order.orderRef == "TastyAgent_CLOSE_1"
