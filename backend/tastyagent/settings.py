"""Environment / .env loading (depends on pydantic-settings).

Kept separate from ``config.py`` so the stdlib-only strategy/risk core never
imports a third-party package. Import this only from the application wiring
(API, scheduler, integration layer) — not from the deterministic core.
"""

from __future__ import annotations

from dataclasses import fields

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .config import RiskLimits, StrategyParams, TradingMode


class _StrategyEnv(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TASTYAGENT_", env_file=".env", extra="ignore")
    min_iv_rank: float | None = None
    min_dte: int | None = None
    max_dte: int | None = None
    target_dte: int | None = None
    max_short_leg_delta: float | None = None
    max_bid_ask_width_pct: float | None = None
    min_open_interest: int | None = None
    min_daily_volume: int | None = None
    earnings_blackout_days: int | None = None
    take_profit_pct: float | None = None
    manage_dte: int | None = None
    stop_loss_multiple: float | None = None


class _RiskEnv(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TASTYAGENT_", env_file=".env", extra="ignore")
    max_trade_bp_pct: float | None = None
    max_total_bp_pct: float | None = None
    max_positions: int | None = None
    max_positions_per_symbol: int | None = None
    max_daily_loss_pct: float | None = None
    consecutive_loss_halt: int | None = None
    kill_switch: bool | None = None


def _merge(defaults, env_model):
    """Overlay any non-None env values onto a frozen dataclass instance."""
    overrides = {
        f.name: getattr(env_model, f.name)
        for f in fields(defaults)
        if getattr(env_model, f.name, None) is not None
    }
    return type(defaults)(**{**defaults.__dict__, **overrides})


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mode: TradingMode = Field(default=TradingMode.SANDBOX, alias="TASTYAGENT_MODE")
    tastytrade_username: str = Field(default="", alias="TASTYTRADE_USERNAME")
    tastytrade_password: str = Field(default="", alias="TASTYTRADE_PASSWORD")
    tastytrade_account: str = Field(default="", alias="TASTYTRADE_ACCOUNT")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-opus-4-8", alias="ANTHROPIC_MODEL")

    def strategy_params(self) -> StrategyParams:
        return _merge(StrategyParams(), _StrategyEnv())

    def risk_limits(self) -> RiskLimits:
        return _merge(RiskLimits(), _RiskEnv())


def load_settings() -> Settings:
    return Settings()
