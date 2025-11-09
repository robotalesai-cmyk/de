# Kucoin Cross-Venue Market Making Bot

```
        +-------------------+       +-------------------+
        |   Data Feeds      |-----> |  Signal Engines   |
        | (Kucoin WS, L2)   |       | (micro, vol, OFI) |
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
        | Execution Router  |<----->| Hedger/Basis      |
        | (SOR, TWAP, VWAP) |       | Capture           |
        +---------+---------+       +----------+--------+
                  |                            |
                  v                            v
        +----------------------------------------------+
        |    Connectors (CCXT live + paper simulator)  |
        +----------------------------------------------+
```

## Overview

This repository contains a production-ready template for a cross-venue crypto market-making bot targeting Kucoin and other venues. The bot combines Avellaneda–Stoikov quoting with microstructure alpha, optional basis/funding capture, and robust risk management.

## Quickstart

### Ready-to-use quickstart

Spin up a fully configured paper-trading bot (and generate editable config files under `~/.mm-bot/`) with a single command:

```bash
poetry run bot-quickstart
```

The command copies `configs/default.yaml` and `configs/venues.yaml` to `~/.mm-bot/`, drops a `.env` template next to them, validates the configuration, and immediately launches the bot in paper mode. To create the files without starting the runtime, pass `--init-only`. Toggle live trading with `--live` after filling in your API keys inside `~/.mm-bot/.env`.

### Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
poetry run pre-commit install
```

Populate `.env` with the generic `EXCHANGE_API_*` keys or venue-specific overrides such as `KUCOIN_API_KEY` before enabling live trading.

### Docker

```bash
docker compose up --build
```

### Paper Trading

```bash
poetry run bot-mm --config configs/default.yaml --paper
```

### Live Trading

Provide Kucoin (or other CCXT venue) API credentials via environment variables and launch without `--paper`:

```bash
KUCOIN_API_KEY=... KUCOIN_API_SECRET=... KUCOIN_API_PASSPHRASE=... \
  poetry run bot-mm --config configs/default.yaml --live
```

The connector automatically falls back to the in-memory simulator whenever credentials are absent, preventing accidental live trading.

### Backtesting

```bash
poetry run bot-backtest --config configs/default.yaml --mode vectorized
```

## Configuration

- `configs/default.yaml`: strategy parameters, symbols, risk caps, hedge policies.
- `configs/venues.yaml`: API endpoints, rate limits, authentication flags.
- per-symbol `max_cancels_per_minute`: optional hard cap on cancellations enforced by the risk engine.

## Safety Notes

- Never load real secrets into the repo; configure via environment variables.
- Start in paper mode and monitor metrics on the Prometheus endpoint.
- Kill switch and orphan reaper protect against stale orders and connectivity loss. Repeated exceptions within the quoting loop trigger the kill switch and halt quoting automatically.

## Known Limitations

- DEX connectors are stubs for illustration.
- Execution models are simplified but structured for extension.
- Backtest fills approximate exchange microstructure; validate before production.

## Testing

```bash
poetry run pytest
```

## Metrics & Observability

A FastAPI service exposes `/health` and `/metrics` for Prometheus scraping.

## License

MIT
