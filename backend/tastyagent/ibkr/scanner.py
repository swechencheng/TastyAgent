"""IBKR Market Scanner for high options volume stock universes.

Replaces Tastytrade's static/curated 'High Options Volume' watchlist by dynamically
querying Interactive Brokers' native Market Scanner.
"""

from __future__ import annotations

import logging
from typing import List

from ib_async import IB, ScannerSubscription

logger = logging.getLogger(__name__)

# Fallback liquid symbols in case the scanner is temporarily unavailable (e.g. outside market hours or network glitch)
FALLBACK_SYMBOLS = [
    "SPY",
    "QQQ",
    "IWM",
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "GOOGL",
    "META",
    "TSLA",
    "AMD",
    "NFLX",
    "COIN",
    "DIS",
    "BA",
    "INTC",
    "PLTR",
    "UBER",
    "BABA",
    "MARA",
]


async def scan_high_options_volume(
    ib: IB,
    scan_code: str = "OPT_VOLUME_MOST_ACTIVE",
    num_rows: int = 25,
    instrument: str = "STK",
    location_code: str = "STK.US.MAJOR",
) -> List[str]:
    """Query IBKR Market Scanner for the most active US options underlyings.

    Args:
        ib: Connected ib_async.IB instance (usually data_ib).
        scan_code: IBKR scan code (e.g. 'OPT_VOLUME_MOST_ACTIVE', 'HIGH_OPT_VOLUME_PUT_CALL_RATIO').
        num_rows: Maximum number of symbols to retrieve.
        instrument: Security instrument ('STK').
        location_code: Market location ('STK.US.MAJOR').

    Returns:
        List of underlying ticker symbols.
    """
    if not ib.isConnected():
        logger.warning("IBKR session not connected; returning fallback symbols.")
        return FALLBACK_SYMBOLS[:num_rows]

    subscription = ScannerSubscription(
        instrument=instrument,
        locationCode=location_code,
        scanCode=scan_code,
        numberOfRows=num_rows,
    )

    try:
        scan_data = await ib.reqScannerDataAsync(subscription)
        symbols: list[str] = []
        for item in scan_data:
            contract = item.contractDetails.contract
            symbol = contract.symbol.strip().upper()
            # Filter out index symbols with special prefixes or empty strings
            if symbol and symbol.isalpha() and symbol not in symbols:
                symbols.append(symbol)

        if symbols:
            logger.info(
                "IBKR Market Scanner returned %d symbols for '%s'",
                len(symbols),
                scan_code,
            )
            return symbols[:num_rows]

        logger.warning("IBKR Market Scanner returned 0 items; using fallback symbols.")
        return FALLBACK_SYMBOLS[:num_rows]

    except Exception as e:
        logger.error(
            "Error executing IBKR market scanner: %s. Using fallback symbols.", e
        )
        return FALLBACK_SYMBOLS[:num_rows]
