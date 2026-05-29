# Backtesting

The Backtesting API provides endpoints for running historical backtests of options strategies. You can create backtests, monitor their progress, retrieve results, and simulate historical trade pricing. Backtests are scoped to the authenticated user.

**Base URL:** `https://api.tastyworks.com`
**Authentication:** Requires a valid session token passed via the `Authorization` header.
**API Version:** 1.0.0

---

## Endpoints

### Get Available Dates

Returns the available historical date ranges for each symbol. Use this to determine what time periods can be backtested for a given underlying.

```
GET /available-dates
```

**Parameters:** None.

**Response** — `200 OK`: Returns available date ranges per symbol.

---

### Get All Backtests

Returns the IDs of all backtests created by the current user.

```
GET /backtests
```

**Parameters:** None.

**Response** — `200 OK`: Returns an array of backtest identifiers.

---

### Create Backtest

Create and start a new backtest with the specified strategy parameters.

```
POST /backtests
```

**Content-Type:** `application/json`

**Request Body:** Strategy configuration including underlying symbol, date range, entry/exit rules, and position sizing parameters.

**Response** — `200 OK`: Returns the created backtest object with its ID.

---

### Get Backtest by ID

Retrieve the full results of a specific backtest.

```
GET /backtests/{id}
```

| Parameter | In | Type | Required | Description |
|-----------|----|------|----------|-------------|
| `id` | path | string | Yes | The backtest ID |

**Response** — `200 OK`: Returns the backtest object including status, parameters, and results.

---

### Cancel Backtest

Cancel a running backtest.

```
POST /backtests/{id}/cancel
```

| Parameter | In | Type | Required | Description |
|-----------|----|------|----------|-------------|
| `id` | path | string | Yes | The backtest ID to cancel |

**Response** — `200 OK`: Confirms cancellation.

---

### Get Backtest Logs

Read the execution logs of a specified backtest. Useful for debugging or understanding the step-by-step execution of the backtest.

```
GET /backtests/{id}/logs
```

| Parameter | In | Type | Required | Description |
|-----------|----|------|----------|-------------|
| `id` | path | string | Yes | The backtest ID |

**Response** — `200 OK`: Returns the log output for the backtest.

---

### Simulate Trade

Returns historical prices for a hypothetical trade. Use this to see what pricing would have been available at a specific point in history without running a full backtest.

```
POST /simulate-trade
```

**Content-Type:** `application/json`

**Request Body:** Trade parameters including symbol, date, and strategy details.

**Response** — `200 OK`: Returns simulated historical pricing data for the trade.

---

## Common Use Cases

- **Strategy validation:** Create a backtest to evaluate how a specific options strategy (e.g., selling 30-delta puts at 45 DTE) would have performed historically.
- **Date range discovery:** Call `GET /available-dates` first to confirm historical data is available for your target symbol and time period before creating a backtest.
- **Quick price check:** Use `POST /simulate-trade` for a one-off historical price lookup without the overhead of a full backtest run.
- **Long-running backtests:** For complex strategies over long time periods, create the backtest, then poll `GET /backtests/{id}` periodically to check status. Use `POST /backtests/{id}/cancel` if needed.

---

## Important Notes

- **User-scoped:** Backtests are tied to the authenticated user, not to a specific account.
- **Asynchronous execution:** Backtests may take time to complete. The create endpoint returns immediately with an ID; poll the get endpoint for results.
- **No request/response schemas in swagger:** The backtesting API swagger does not define detailed request/response schemas. Refer to the developer.tastytrade.com documentation for complete parameter details.
