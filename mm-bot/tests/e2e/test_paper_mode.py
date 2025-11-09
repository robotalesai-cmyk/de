from __future__ import annotations

import asyncio
import pathlib

from bot.connectors.cex_ccxt import ExchangeConnector
from bot.core.events import EventBus
from bot.core.metrics import MetricsCollector
from bot.core.types import OrderBookSnapshot, Trade
from bot.data.feeds import InMemoryFeedStore, SNAPSHOT_TOPIC, TRADE_TOPIC, SyntheticFeed
from bot.data.storage import create_storage
from bot.hedge.hedger import HedgePolicy, Hedger
from bot.models.avellaneda_stoikov import AvellanedaStoikovModel
from bot.mm.quoter import Quoter
from bot.risk.limits import RiskLimits, SymbolLimits
from bot.risk.orphan_reaper import OrphanReaper
from bot.signals.impact import ImpactEstimator
from bot.signals.microstructure import MicrostructureSignals
from bot.signals.volatility import VolatilityEstimator


def test_paper_mode_generates_metrics(tmp_path: pathlib.Path) -> None:
    asyncio.run(_run_paper_mode(tmp_path))


async def _run_paper_mode(tmp_path: pathlib.Path) -> None:
    bus = EventBus()
    store = InMemoryFeedStore()
    micro = MicrostructureSignals()
    vol = VolatilityEstimator()
    impact = ImpactEstimator()
    collector = MetricsCollector()
    db_path = tmp_path / "paper.db"
    storage = await create_storage("sqlite", f"sqlite:///{db_path}")
    connector = ExchangeConnector(venue="kucoin", paper=True)
    await connector.start()

    async def on_snapshot(snapshot: OrderBookSnapshot) -> None:
        micro.update_snapshot(snapshot)
        vol.update(snapshot)

    async def on_trade(trade: Trade) -> None:
        micro.update_trade(trade)

    await bus.subscribe(SNAPSHOT_TOPIC, on_snapshot)
    await bus.subscribe(TRADE_TOPIC, on_trade)

    feed = SyntheticFeed(bus, "kucoin", "BTC-PERP", base_price=30000)
    feed_task = asyncio.create_task(feed.run(store))

    model = AvellanedaStoikovModel(gamma=0.1, horizon=10, kappa=1.0, min_spread=0.1, skew_alpha=0.0)
    risk = RiskLimits(
        {"BTC-PERP": SymbolLimits(max_position=1.0, max_order_notional=10000.0)},
        max_drawdown=10_000.0,
        max_daily_loss=5_000.0,
        max_inventory_notional=20_000.0,
    )
    hedge = Hedger(connector, HedgePolicy(enabled=True, threshold=0.1, max_notional=1000.0))
    orphan = OrphanReaper(connector)
    quoter = Quoter(
        store=store,
        connector=connector,
        model=model,
        risk=risk,
        micro=micro,
        vol=vol,
        impact=impact,
        hedger=hedge,
        orphan=orphan,
        storage=storage,
        refresh=0.2,
        lot_size=0.01,
        tick_size=0.1,
        venue="kucoin",
        symbol="BTC-PERP",
        metrics=collector,
    )
    quoter_task = asyncio.create_task(quoter.start())

    await asyncio.sleep(2.5)
    feed.stop()
    quoter_task.cancel()
    await asyncio.gather(feed_task, quoter_task, return_exceptions=True)
    await connector.close()
    await storage.close()

    assert quoter._state.last_quote is not None
