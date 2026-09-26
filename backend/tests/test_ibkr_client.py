from unittest.mock import MagicMock
import pytest

from tastyagent.ibkr.client import IBKRClient
from tastyagent.settings import Settings


def test_ibkr_client_initialization():
    settings = Settings(
        ibkr_host="127.0.0.1",
        ibkr_port=4002,
        ibkr_client_id=77,
        ibkr_account="U999999",
        ibkr_data_host="127.0.0.1",
        ibkr_data_port=4001,
        ibkr_data_client_id=78,
    )
    client = IBKRClient(settings)
    assert client.settings.ibkr_host == "127.0.0.1"
    assert client.settings.ibkr_port == 4002
    assert client.settings.ibkr_client_id == 77
    assert client.settings.ibkr_account == "U999999"
    assert not client.is_connected


def test_ibkr_client_account_fallback_when_empty():
    settings = Settings(ibkr_account="")
    client = IBKRClient(settings)
    client.trading_ib = MagicMock()
    client.trading_ib.managedAccounts.return_value = ["DUP12345"]
    assert client.account == "DUP12345"


def test_ibkr_client_contract_details_patch():
    # Verify monkey patch is applied to ib_async.wrapper.Wrapper.contractDetails
    import ib_async.wrapper

    wrapper = ib_async.wrapper.Wrapper(ib=MagicMock())
    # If reqId not in results, it should silently return without error
    wrapper._results = {}
    wrapper.contractDetails(reqId=99999, contractDetails=None)
