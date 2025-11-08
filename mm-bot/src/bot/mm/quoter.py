"""Market making quote engine."""

from __future__ import annotations

import asyncio
import logging
import math
from dataclasses import dataclass, field
from typing import Dict, Optional, Protocol

from ..connectors.cex_ccxt import ExchangeConnector, OrderState
from ..core.types import Order, OrderBookSnapshot, Side, Trade
from ..core.utils import jitter_sleep
from ..data.feeds import InMemoryFeedStore
from ..data.storage import StorageBackend
from ..models.avellaneda_stoikov import AvellanedaStoikovModel, QuoteResult
from ..risk.limits import RiskLimits
from ..risk.orphan_reaper import OrphanReaper
from ..risk.kill_switch import KillSwitch
from ..signals.microstructure import MicrostructureSignals
from ..signals.volatility import VolatilityEstimator
from ..signals.impact import ImpactEstimator
from ..hedge.hedger import Hedger


class MetricsRecorder(Protocol):
    def record(self, symbol: str, inventory: float, pnl: float, spread: float) -> None:  # pragma: no cover - interface
        ...


@dataclass
class SymbolState:
    inventory: float = 0.0
    pnl: float = 0.0
    last_quote: Optional[QuoteResult] = None
    open_orders: Dict[Side, OrderState] = field(default_factory=dict)


class Quoter:
    def __init__(
        self,
        store: InMemoryFeedStore,
        connector: ExchangeConnector,
        model: AvellanedaStoikovModel,
        risk: RiskLimits,
        micro: MicrostructureSignals,
        vol: VolatilityEstimator,
        impact: ImpactEstimator,
        hedger: Hedger,
        orphan: OrphanReaper,
        storage: StorageBackend,
        refresh: float,
        lot_size: float,
        tick_size: float,
        venue: str,
        symbol: str,
        metrics: Optional[MetricsRecorder] = None,
        kill_switch: Optional[KillSwitch] = None,
    ) -> None:
        self._store = store
        self._connector = connector
        self._model = model
        self._risk = risk
        self._micro = micro
        self._vol = vol
        self._impact = impact
        self._hedger = hedger
        self._orphan = orphan
        self._storage = storage
        self._refresh = refresh
        self._lot_size = lot_size
        self._tick_size = tick_size
        self._venue = venue
        self._symbol = symbol
        self._state = SymbolState()
        self._running = False
        self._metrics = metrics
        self._kill_switch = kill_switch
        self._logger = logging.getLogger(f"Quoter[{symbol}]")
        self._connector.register_symbol(symbol)

    async def start(self) -> None:
        self._running = True
        try:
            while self._running:
                if self._risk.halted:
                    self._logger.warning("risk halted for %s: %s", self._symbol, self._risk.halted_reason)
                    await self._cancel_all()
                    await asyncio.sleep(1.0)
                    break
                if self._kill_switch and self._kill_switch.tripped:
                    self._logger.error("kill switch tripped: %s", self._kill_switch.reason)
                    await self._cancel_all()
                    break
                try:
                    snapshot = await self._store.get_snapshot(self._symbol)
                    if snapshot is None:
                        await asyncio.sleep(0.1)
                        continue
                    feature = self._micro.get(self._symbol)
                    if feature is None:
                        await asyncio.sleep(0.1)
                        continue
                    self._risk.update_mid(self._symbol, snapshot.mid)
                    sigma = self._vol.sigma(self._symbol)
                    lam = self._impact.get(self._symbol)
                    quote = self._model.generate_quotes(
                        snapshot=snapshot,
                        inventory=self._state.inventory,
                        sigma=sigma,
                        feature=feature,
                        tick_size=self._tick_size,
                        min_tick_spread=self._tick_size,
                        impact_lambda=lam,
                    )
                    self._state.last_quote = quote
                    await self._storage.record_snapshot(snapshot)
                    await self._replace_orders(quote)
                    await self._connector.process_cross(self._symbol, snapshot.bid.price, snapshot.ask.price)
                    await self._drain_fills(snapshot)
                    if self._risk.halted:
                        continue
                    hedged_inventory = await self._hedger.maybe_hedge(
                        snapshot, self._state.inventory, self._tick_size, self._lot_size
                    )
                    self._state.inventory = hedged_inventory
                    self._risk.update_inventory(self._symbol, self._state.inventory)
                    if self._metrics:
                        self._metrics.record(
                            self._symbol, self._state.inventory, self._state.pnl, quote.spread
                        )
                        self._metrics.hedge_notional = getattr(self._hedger, "last_notional", 0.0)
                    await self._orphan.sweep()
                except Exception as exc:
                    self._logger.exception("error in quoting loop: %s", exc)
                    if self._kill_switch:
                        await self._kill_switch.record_error(str(exc))
                    await asyncio.sleep(min(self._refresh, 1.0))
                await jitter_sleep(self._refresh)
        finally:
            await self._cancel_all()

    async def stop(self) -> None:
        self._running = False

    async def _replace_orders(self, quote: QuoteResult) -> None:
        open_orders = await self._connector.list_open_orders(symbol=self._symbol)
        desired_prices = {Side.BUY: quote.bid, Side.SELL: quote.ask}
        active_sides: Dict[Side, OrderState] = {}
        for state in open_orders:
            target = desired_prices[state.order.side]
            if math.isclose(state.order.price, target, abs_tol=self._tick_size / 2):
                active_sides[state.order.side] = state
                continue
            if state.order.order_id:
                await self._connector.cancel_order(state.order.order_id, symbol=self._symbol)
                self._risk.record_cancel(self._symbol)
        self._state.open_orders = active_sides
        for side, price in desired_prices.items():
            if side in active_sides:
                continue
            order = Order(
                venue=self._venue,
                symbol=self._symbol,
                side=side,
                price=price,
                size=self._lot_size,
                post_only=True,
            )
            if not self._risk.check_order(order):
                continue
            order_id = await self._connector.place_order(order)
            await self._orphan.track(order_id)
            order_with_id = Order(
                venue=order.venue,
                symbol=order.symbol,
                side=order.side,
                price=order.price,
                size=order.size,
                order_id=order_id,
                post_only=order.post_only,
            )
            self._state.open_orders[side] = OrderState(order=order_with_id, remaining=order.size)

    async def _drain_fills(self, snapshot: OrderBookSnapshot) -> None:
        while True:
            fill = await self._connector.poll_fill()
            if fill is None:
                break
            pnl_delta = (snapshot.mid - fill.price) * (fill.size if fill.side == Side.SELL else -fill.size)
            self._state.pnl += pnl_delta - fill.fee
            self._state.inventory += fill.size if fill.side == Side.BUY else -fill.size
            self._risk.record_fill(fill, snapshot.mid, pnl_delta - fill.fee)
            await self._storage.record_trade(
                Trade(
                    venue=fill.venue,
                    symbol=fill.symbol,
                    timestamp=snapshot.timestamp,
                    price=fill.price,
                    size=fill.size,
                    side=fill.side,
                )
            )

    async def _cancel_all(self) -> None:
        orders = await self._connector.list_open_orders(symbol=self._symbol)
        for state in orders:
            if state.order.order_id:
                await self._connector.cancel_order(state.order.order_id, symbol=self._symbol)
