# Cross-Venue Crypto Market-Making Bot

```
        +-------------------+       +-------------------+
        |   Market Data     |-----> |  Signal Engines   |
        | (CEX & DEX feeds) |       | (micro, vol, λ)   |
        +---------+---------+       +----------+--------+
                  |                            |
                  v                            v
        +-------------------+       +-------------------+
        | Avellaneda-Stoikov|<----->| Risk Engine       |
        | Quote Generator   |       | (limits, kill)    |
        +---------+---------+       +----------+--------+
                  |                            |
                  v                            v
        +-------------------+       +-------------------+
        | Execution Router  |<----->| Hedge/Basis       |
        | (SOR, TWAP/VWAP)  |       | Capture           |
        +---------+---------+       +----------+--------+
                  |                            |
                  v                            v
        +-----------------------------------------------+
        |  Connectors (CCXT venues + DEX stubs/paper)   |
        +-----------------------------------------------+
```

## Overview

This repository contains a production-grade template for a cross-venue crypto market-making
system written for Python 3.11. The engine combines:

- Avellaneda–Stoikov quoting with microstructure adjustments (microprice, queue/order-flow
  imbalance, short-horizon volatility, and Kyle's λ impact gating).
- Automatic delta hedging (perp or spot) with TWAP/VWAP execution helpers.
- Optional basis/funding capture across perp/spot or perp/perp venues.
- Multi-venue connectors (CCXT based CEX + typed DEX stubs) wrapped in a smart order router.
- Robust risk controls (inventory caps, drawdown, cancel rate, kill switch, orphan reaper).
- Prometheus metrics and FastAPI health endpoint.
- Event-driven and vectorized backtesting modes.

The default configuration targets BTC across a perp + spot venue in paper trading mode. Live
trading requires providing exchange credentials via environment variables.

## Quickstart

### Local (Poetry)

```bash
python -m venv .venv
source .venv/bin/activate
pip install poetry
poetry install
cp .env.example .env
poetry run pre-commit install
```

Run the bot in paper mode:

```bash
poetry run bot-mm --config configs/default.yaml --paper
```

Switch to live trading by providing venue credentials (example for Kucoin):

```bash
KUCOIN_API_KEY=... KUCOIN_API_SECRET=... KUCOIN_API_PASSPHRASE=... \
  poetry run bot-mm --config configs/default.yaml --live
```

### Docker Compose

```bash
docker compose up --build
```

The compose stack includes ClickHouse for optional data persistence. Comment the dependency in
`docker-compose.yml` if ClickHouse is not required.

### Backtesting

```bash
poetry run bot-backtest --config configs/default.yaml --mode vectorized
poetry run bot-backtest --config configs/default.yaml --mode event
```

Both modes emit a CSV file with PnL/risk metrics and print a console summary (Sharpe, Sortino,
turnover, hit-rate, drawdowns, capacity proxy).

## Configuration

- `configs/default.yaml` – strategy setup: symbols, fee tiers, maker/taker flags, post-only
  preference, account caps, inventory targets, hedge/basis policies, and risk thresholds.
- `configs/venues.yaml` – venue metadata including REST/WS endpoints and rate-limit policies.
- `.env.example` – environment variables for CCXT credentials and optional ClickHouse access.

Runtime secrets are loaded from environment variables of the form `<VENUE>_API_KEY` with a
generic `EXCHANGE_API_*` fallback.

## Modules

- `bot/core/` – configuration loading, events, typed dataclasses, metrics.
- `bot/data/` – websocket/synthetic feeds and persistence helpers (SQLite/ClickHouse).
- `bot/signals/` – microstructure, volatility, and impact estimators.
- `bot/models/` – Avellaneda–Stoikov quoting and Hawkes process placeholder.
- `bot/mm/` – market-maker core loop coordinating risk, quoting, and execution.
- `bot/hedge/` – delta hedge policy + TWAP executor.
- `bot/basis/` – funding/basis capture state machine.
- `bot/exec/` – routing and execution schedules (SOR/TWAP/VWAP).
- `bot/connectors/` – CCXT wrapper with paper simulator and DEX stub interface.
- `bot/risk/` – inventory/drawdown limits, kill-switch, orphan reaper.
- `bot/cli/` – CLI entrypoints for market making and backtesting.
- `tests/` – unit, property-based, and e2e (paper mode) tests.

## Metrics & Observability

`MetricsService` exposes:

- `pnl_realized`, `pnl_unrealized`
- `inventory`
- `spread_target`
- `fill_rate`
- `hedge_notional`
- `funding_accrual`
- `error_rate`

Scrape the `/metrics` endpoint via Prometheus. `/health` returns a basic status document.

## Safety Notes

- Always begin in paper mode. Verify fills, inventory, and hedging behaviour before switching to
  live trading.
- Provide API keys through environment variables only; never commit credentials to source control.
- The kill switch trips on repeated errors and cancels open orders. The orphan reaper sweeps stale
  orders if websocket desyncs occur.
- Funding/basis capture is optional and capped; review risk parameters carefully.

## Known Limitations

- DEX connectors are illustrative stubs; integrate venue-specific signing and settlement before
  production deployment.
- Market impact and queue-position models are simplified. Extend with venue-specific order book
  models for production alpha.
- Backtesting uses synthetic data loaders; plug in your historical L2/trade archives for realistic
  fills.

## Testing

```bash
poetry run pytest
```

CI can be enabled via GitHub Actions using the provided workflow (runs linting, typing, tests).

## License

MIT
