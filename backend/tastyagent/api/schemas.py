"""Pydantic response models for the dashboard API."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class LegOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    option_type: str
    strike: float
    expiration: date
    action: str
    quantity: int
    delta: float


class TradeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    symbol: str
    strategy: str
    contracts: int
    status: str
    mode: str
    rationale: str
    entry_credit: float
    buying_power: float
    dte_at_entry: int
    current_cost_to_close: float
    unrealized_pnl: float
    probability_of_profit: float
    realized_pnl: float | None
    exit_reason: str | None
    is_win: bool | None
    opened_at: datetime | None
    closed_at: datetime | None
    legs: list[LegOut]


class PnLOut(BaseModel):
    realized_pnl: float
    unrealized_pnl: float
    total_pnl: float
    open_count: int
    closed_count: int
    wins: int
    losses: int
    win_rate: float | None
    profit_pct: float | None
    starting_capital: float


class StatusOut(BaseModel):
    mode: str
    kill_switch: bool
    market_open: bool
    starting_capital: float
    requires_approval: bool
    scheduler_running: bool = False


class BenchmarkPoint(BaseModel):
    date: date
    value: float


class BenchmarkOut(BaseModel):
    strategy_return_pct: float
    sp500_return_pct: float
    outperformance_pct: float
    strategy_curve: list[BenchmarkPoint]
    sp500_curve: list[BenchmarkPoint]


class ActionResult(BaseModel):
    trade_id: int
    symbol: str
    action: str
    detail: str = ""


class ModeRequest(BaseModel):
    mode: str


class KillSwitchRequest(BaseModel):
    engaged: bool


class WatchlistItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    symbol: str
    enabled: bool
    source: str


class WatchlistAdd(BaseModel):
    symbol: str


class WatchlistImport(BaseModel):
    symbols: list[str]
    source: str = "imported"


class ToggleRequest(BaseModel):
    enabled: bool


class RankedSymbol(BaseModel):
    symbol: str
    iv_rank: float | None
    iv_percentile: float | None
    liquidity_rating: int | None


class TastytradeWatchlist(BaseModel):
    name: str
    group: str | None = None
    symbols: list[str]
