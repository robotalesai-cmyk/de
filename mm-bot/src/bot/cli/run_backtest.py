"""Backtesting entrypoint."""

from __future__ import annotations

import csv
import random
from dataclasses import dataclass
from pathlib import Path
from typing import List

import click

from ..core.config import StrategyConfig
from ..core.types import Side
from ..core.utils import annualized_sharpe
from ..models.avellaneda_stoikov import AvellanedaStoikovModel


@dataclass
class BacktestResult:
    pnl: float
    sharpe: float
    sortino: float
    trades: int
    turnover: float
    hit_rate: float
    max_drawdown: float
    capacity: float


def _simulate_prices(steps: int, start: float = 30000.0) -> List[float]:
    prices = [start]
    for _ in range(steps - 1):
        drift = random.uniform(-40, 40)
        prices.append(max(prices[-1] + drift, 1.0))
    return prices


def _sortino(returns: List[float]) -> float:
    downside = [min(0.0, r) for r in returns]
    downside_variance = sum(d**2 for d in downside) / max(len(downside), 1)
    if downside_variance == 0:
        return 0.0
    mean = sum(returns) / len(returns)
    return mean / (downside_variance**0.5)


def _max_drawdown(equity: List[float]) -> float:
    peak = equity[0]
    max_dd = 0.0
    for value in equity:
        peak = max(peak, value)
        max_dd = min(max_dd, value - peak)
    return abs(max_dd)


def _run_simulation(config: StrategyConfig, steps: int, event_mode: bool = False) -> BacktestResult:
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
    cash = 0.0
    trades = 0
    turnover = 0.0
    trade_pnls: List[float] = []
    returns: List[float] = []
    equity_curve: List[float] = [0.0]
    maker_fee = symbol.maker_fee_bps / 10_000.0 if hasattr(symbol, "maker_fee_bps") else 0.0

    queue_bias = 0.0
    for idx, price in enumerate(prices):
        sigma = 0.02 + 0.01 * abs(queue_bias)
        ofi = random.uniform(-0.1, 0.1)
        queue_bias = 0.7 * queue_bias + 0.3 * ofi
        micro_feature = type(
            "Feature",
            (),
            {
                "order_flow_imbalance": ofi,
                "queue_imbalance": queue_bias,
                "microprice": price * (1 + 0.0005 * ofi),
            },
        )
        snapshot = type("Snap", (), {"mid": price})
        quote = model.generate_quotes(
            snapshot=snapshot,  # type: ignore[arg-type]
            inventory=inventory,
            sigma=sigma,
            feature=micro_feature,
            tick_size=symbol.tick_size,
            min_tick_spread=symbol.tick_size,
            impact_lambda=abs(queue_bias) * 0.1,
        )
        activity_factor = 0.6 if event_mode else 0.5
        fill_prob = activity_factor + 0.4 * max(-0.25, min(0.25, ofi))
        if random.random() > fill_prob:
            equity_curve.append(cash + inventory * price)
            returns.append((price - prices[0]) / prices[0])
            continue
        take_side = Side.BUY if random.random() < 0.5 + ofi else Side.SELL
        fill_price = quote.ask if take_side == Side.BUY else quote.bid
        signed = symbol.lot_size if take_side == Side.BUY else -symbol.lot_size
        fee = abs(fill_price * signed) * maker_fee
        cash -= fill_price * signed + fee
        inventory += signed
        turnover += abs(signed * fill_price)
        trade_pnl = -fill_price * signed - fee
        trade_pnls.append(trade_pnl)
        trades += 1
        equity_curve.append(cash + inventory * price)
        returns.append((price - prices[0]) / prices[0])

    final_pnl = cash + inventory * prices[-1]
    sharpe = annualized_sharpe(returns)
    sortino = _sortino(returns)
    hit_rate = sum(1 for pnl in trade_pnls if pnl > 0) / max(len(trade_pnls), 1)
    drawdown = _max_drawdown(equity_curve)
    capacity = turnover / max(steps, 1)
    return BacktestResult(
        pnl=final_pnl,
        sharpe=sharpe,
        sortino=sortino,
        trades=trades,
        turnover=turnover,
        hit_rate=hit_rate,
        max_drawdown=drawdown,
        capacity=capacity,
    )


def _vectorized_backtest(config: StrategyConfig, steps: int = 200) -> BacktestResult:
    return _run_simulation(config, steps, event_mode=False)


def _event_driven_backtest(config: StrategyConfig, steps: int = 200) -> BacktestResult:
    return _run_simulation(config, steps, event_mode=True)


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
    fieldnames = [
        "pnl",
        "sharpe",
        "sortino",
        "trades",
        "turnover",
        "hit_rate",
        "max_drawdown",
        "capacity",
    ]
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(result.__dict__)
    click.echo(
        "Backtest complete. "
        f"PnL={result.pnl:.2f} Sharpe={result.sharpe:.2f} "
        f"Sortino={result.sortino:.2f} HitRate={result.hit_rate:.2%} "
        f"MaxDD={result.max_drawdown:.2f}"
    )


if __name__ == "__main__":
    main()
