"""Backtesting entrypoint."""

from __future__ import annotations

import csv
import random
from dataclasses import dataclass
from pathlib import Path
from typing import List

import click

from ..core.config import StrategyConfig
from ..core.utils import annualized_sharpe
from ..models.avellaneda_stoikov import AvellanedaStoikovModel


@dataclass
class BacktestResult:
    pnl: float
    sharpe: float
    trades: int
    turnover: float


def _simulate_prices(steps: int, start: float = 30000.0) -> List[float]:
    prices = [start]
    for _ in range(steps - 1):
        drift = random.uniform(-50, 50)
        prices.append(max(prices[-1] + drift, 1.0))
    return prices


def _vectorized_backtest(config: StrategyConfig, steps: int = 200) -> BacktestResult:
    symbol = config.symbols[0]
    model = AvellanedaStoikovModel(
        gamma=config.quote.gamma,
        horizon=config.quote.horizon_seconds,
        kappa=config.quote.kappa,
        min_spread=config.quote.min_spread,
        skew_alpha=config.quote.skew_alpha,
    )
    prices = _simulate_prices(steps)
    inventory = 0.0
    pnl = 0.0
    returns = []
    trades = 0
    turnover = 0.0
    for price in prices:
        sigma = 0.02
        micro_feature = type("Feature", (), {"order_flow_imbalance": 0.0, "queue_imbalance": 0.0})
        snapshot = type("Snap", (), {"mid": price})
        quote = model.generate_quotes(
            snapshot=snapshot,  # type: ignore[arg-type]
            inventory=inventory,
            sigma=sigma,
            feature=micro_feature,
            tick_size=symbol.tick_size,
            min_tick_spread=symbol.tick_size,
            impact_lambda=0.0,
        )
        fill_price = quote.bid if random.random() > 0.5 else quote.ask
        signed = symbol.lot_size if fill_price == quote.bid else -symbol.lot_size
        inventory += signed
        pnl -= signed * fill_price
        turnover += abs(signed * fill_price)
        trades += 1
        returns.append((price - prices[0]) / prices[0])
    sharpe = annualized_sharpe(returns)
    pnl += inventory * prices[-1]
    return BacktestResult(pnl=pnl, sharpe=sharpe, trades=trades, turnover=turnover)


def _event_driven_backtest(config: StrategyConfig, steps: int = 200) -> BacktestResult:
    # Simplified event driven: reuse vectorized results
    return _vectorized_backtest(config, steps)


@click.command()
@click.option("--config", "config_path", type=click.Path(exists=True, path_type=Path), default=Path("configs/default.yaml"))
@click.option("--mode", type=click.Choice(["vectorized", "event"]), default="vectorized")
@click.option("--output", type=click.Path(path_type=Path), default=Path("backtest.csv"))
def main(config_path: Path, mode: str, output: Path) -> None:
    config = StrategyConfig.load(config_path)
    if mode == "vectorized":
        result = _vectorized_backtest(config)
    else:
        result = _event_driven_backtest(config)
    fieldnames = ["pnl", "sharpe", "trades", "turnover"]
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(result.__dict__)
    click.echo(f"Backtest complete. PnL={result.pnl:.2f}, Sharpe={result.sharpe:.2f}")


if __name__ == "__main__":
    main()
