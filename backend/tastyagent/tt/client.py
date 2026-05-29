"""TastyTrade session client: OAuth session + rate-limited account access.

Wraps the tastyware ``tastytrade`` SDK (v12, async, OAuth-only). The trading
mode decides the environment: BACKTEST/SANDBOX use the cert (paper) environment
(``is_test=True``); LIVE_* use production. Each environment needs its own OAuth
credentials.

Verified against the sandbox: ``Session(client_secret, refresh_token,
is_test=True)`` authenticates and token refresh is handled by the SDK. All
account calls are async and funnelled through the token-bucket limiter.
"""

from __future__ import annotations

from tastytrade import Account, Session

from ..config import TradingMode
from .ratelimit import AsyncTokenBucket


class NoAccountsError(RuntimeError):
    """Raised when an authenticated session has no trading accounts.

    In the sandbox this means no paper account is provisioned for / linked to
    the OAuth grant yet.
    """


class TastytradeClient:
    def __init__(
        self,
        client_secret: str,
        refresh_token: str,
        mode: TradingMode,
        *,
        limiter: AsyncTokenBucket | None = None,
        account_number: str | None = None,
    ) -> None:
        self._client_secret = client_secret
        self._refresh_token = refresh_token
        self.mode = mode
        self.account_number = account_number or None
        self.limiter = limiter or AsyncTokenBucket()
        self._session: Session | None = None

    @property
    def is_test(self) -> bool:
        """Cert (paper) environment for everything except live trading."""
        return not self.mode.is_live

    def connect(self) -> Session:
        """Create (or recreate) the OAuth session. Synchronous in the SDK.

        A 30s timeout is passed through to httpx because sandbox order/management
        endpoints are slow and the httpx default times out prematurely.
        """
        self._session = Session(
            self._client_secret,
            self._refresh_token,
            is_test=self.is_test,
            timeout=30,
        )
        return self._session

    @property
    def session(self) -> Session:
        if self._session is None:
            self.connect()
        assert self._session is not None
        return self._session

    async def accounts(self) -> list[Account]:
        await self.limiter.acquire()
        return await Account.get(self.session)

    async def primary_account(self) -> Account:
        """Return the configured account, else the first one available."""
        accts = await self.accounts()
        if not accts:
            raise NoAccountsError(
                "Authenticated but no trading accounts on this session. "
                "Provision/link a sandbox account to this OAuth grant."
            )
        if self.account_number:
            for a in accts:
                if a.account_number == self.account_number:
                    return a
            raise NoAccountsError(
                f"Account {self.account_number!r} not found among "
                f"{[a.account_number for a in accts]}"
            )
        return accts[0]


def from_settings(settings) -> TastytradeClient:
    """Build a client from a loaded ``settings.Settings`` instance."""
    import os

    return TastytradeClient(
        client_secret=os.environ.get("TASTYTRADE_CLIENT_SECRET", ""),
        refresh_token=os.environ.get("TASTYTRADE_OAUTH_REFRESH_TOKEN", ""),
        mode=settings.mode,
        account_number=settings.tastytrade_account or None,
    )


def metrics_session_from_env() -> Session | None:
    """Build a PRODUCTION read-only session for market metrics (IV rank).

    Market metrics are not served in the sandbox, so IV rank — a core entry
    guardrail input — must come from production. This uses a separate read-only
    grant (no trade scope) so it cannot place orders. Returns None if the prod
    read credentials aren't configured, letting callers fall back / surface the
    gap explicitly.
    """
    import os

    secret = os.environ.get("TASTYTRADE_PROD_CLIENT_SECRET")
    refresh = os.environ.get("TASTYTRADE_PROD_OAUTH_REFRESH_TOKEN")
    if not (secret and refresh):
        return None
    return Session(secret, refresh, is_test=False, timeout=30)
