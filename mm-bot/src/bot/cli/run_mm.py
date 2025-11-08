"""Run the market making bot."""

from __future__ import annotations

import asyncio
import logging
import signal
from pathlib import Path
from typing import Dict

import click

from ..basis.funding import FundingCapture, FundingPolicy
from ..connectors.cex_ccxt import ExchangeConnector
from ..core.config import StrategyConfig, load_venues_config
from ..core.events import EventBus
from ..core.metrics import MetricsCollector, MetricsService
from ..core.utils import load_exchange_credentials
from ..data.feeds import (
    InMemoryFeedStore,
    SNAPSHOT_TOPIC,
    TRADE_TOPIC,
    KucoinFeed,
    SyntheticFeed,
)
from ..data.storage import create_storage
from ..hedge.hedger import HedgePolicy, Hedger
from ..models.avellaneda_stoikov import AvellanedaStoikovModel
from ..mm.quoter import Quoter
from ..risk.kill_switch import KillSwitch
from ..risk.limits import RiskLimits, SymbolLimits
from ..risk.orphan_reaper import OrphanReaper
from ..signals.impact import ImpactEstimator
from ..signals.microstructure import MicrostructureSignals
from ..signals.volatility import VolatilityEstimator

logger = logging.getLogger("bot")


async def _run(config_path: Path, paper: bool) -> None:
    config = StrategyConfig.load(config_path)
    collector = MetricsCollector()
    metrics_service = MetricsService(collector, config.metrics.host, config.metrics.port)
    await metrics_service.start()
    bus = EventBus()
    store = InMemoryFeedStore()
    micro = MicrostructureSignals()
    vol = VolatilityEstimator()
    impact = ImpactEstimator()
    last_trade_price: Dict[str, float] = {}

    storage = await create_storage(config.storage.backend, config.storage.dsn)
    venues = load_venues_config(config.venues_config)
    connectors: Dict[str, ExchangeConnector] = {}

    for venue_name in {symbol_cfg.venue for symbol_cfg in config.symbols}:
        venue_info = venues.get(venue_name)
        credentials = load_exchange_credentials(venue_name)
        use_paper = paper or credentials is None
        if not use_paper and credentials is None:
            raise RuntimeError(f"Missing credentials for live trading on {venue_name}")
        connector = ExchangeConnector(
            venue=venue_name,
            paper=use_paper,
            credentials=None if use_paper else credentials,
            sandbox=paper and venue_info.has_paper,
        )
        await connector.start()
        connectors[venue_name] = connector
    funding = FundingCapture(
        FundingPolicy(
            enabled=config.basis.enabled,
            max_notional=config.basis.max_notional,
            threshold=config.basis.funding_threshold,
        )
    )

    risk_limits = RiskLimits(
        {
            symbol_cfg.name: SymbolLimits(
                max_position=symbol_cfg.max_position,
                max_order_notional=symbol_cfg.max_order_notional,
                max_cancels_per_minute=symbol_cfg.max_cancels_per_minute,
            )
            for symbol_cfg in config.symbols
        },
        max_drawdown=config.risk.max_drawdown,
        max_daily_loss=config.risk.max_daily_loss,
        max_inventory_notional=config.risk.max_inventory_notional,
    )

    stop_event = asyncio.Event()

    async def on_kill(reason: str) -> None:
        logger.error("Kill switch triggered: %s", reason)
        collector.error_rate = 1.0
        stop_event.set()

    kill_switch = KillSwitch(config.risk.kill_switch_threshold, on_kill)

    async def handle_snapshot(snapshot) -> None:
        micro.update_snapshot(snapshot)
        vol.update(snapshot)

    async def handle_trade(trade) -> None:
        micro.update_trade(trade)
        prev = last_trade_price.get(trade.symbol, trade.price)
        if prev > 0:
            price_return = (trade.price - prev) / prev
            impact.update(trade, price_return)
        last_trade_price[trade.symbol] = trade.price
        collector.funding_accrual = funding.accrual()

    await bus.subscribe(SNAPSHOT_TOPIC, handle_snapshot)
    await bus.subscribe(TRADE_TOPIC, handle_trade)

    feeds = []
    tasks = []

    for symbol_cfg in config.symbols:
        connector = connectors[symbol_cfg.venue]
        if paper:
            feed = SyntheticFeed(bus, symbol_cfg.venue, symbol_cfg.name, base_price=30000)
        else:
            feed = KucoinFeed(
                bus,
                symbol_cfg.venue,
                symbol_cfg.name,
                subscription_symbol=symbol_cfg.name,
            )
        feeds.append(feed)
        tasks.append(asyncio.create_task(feed.run(store)))
        model = AvellanedaStoikovModel(
            gamma=config.quote.gamma,
            horizon=config.quote.horizon_seconds,
            kappa=config.quote.kappa,
            min_spread=config.quote.min_spread,
            skew_alpha=config.quote.skew_alpha,
        )
        hedge = Hedger(
            connector,
            HedgePolicy(
                enabled=config.hedge.enabled,
                threshold=config.hedge.rebalance_threshold,
                max_notional=config.hedge.max_notional,
            ),
        )
        orphan = OrphanReaper(connector)
        quoter = Quoter(
            store=store,
            connector=connector,
            model=model,
            risk=risk_limits,
            micro=micro,
            vol=vol,
            impact=impact,
            hedger=hedge,
            orphan=orphan,
            storage=storage,
            refresh=config.quote.refresh_seconds,
            lot_size=symbol_cfg.lot_size,
            tick_size=symbol_cfg.tick_size,
            venue=symbol_cfg.venue,
            symbol=symbol_cfg.name,
            metrics=collector,
            kill_switch=kill_switch,
        )
        tasks.append(asyncio.create_task(quoter.start()))

    def _handle_signal(*_: int) -> None:
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handle_signal)
        except NotImplementedError:  # pragma: no cover - windows
            pass

    logger.info("Bot started in %s mode", "paper" if paper else "live")

    try:
        await stop_event.wait()
    finally:
        for feed in feeds:
            feed.stop()
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        for connector in connectors.values():
            await connector.close()
        await metrics_service.stop()
        await storage.close()


@click.command()
@click.option("--config", "config_path", type=click.Path(exists=True, path_type=Path), default=Path("configs/default.yaml"))
@click.option("--paper/--live", default=True, help="Run in paper trading mode")
def main(config_path: Path, paper: bool) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    try:
        import uvloop  # type: ignore[import-not-found]
        uvloop.install()
    except ImportError:
        pass
    try:
        asyncio.run(_run(config_path, paper))
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")


if __name__ == "__main__":
    main()
