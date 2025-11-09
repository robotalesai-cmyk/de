from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Dict, Optional, Protocol

from ..connectors.cex_ccxt import ExchangeConnector, OrderState
from ..core.config import SymbolConfig
from ..core.types import Fill, Order, OrderBookSnapshot, Side, Trade
from ..core.utils import jitter_sleep
from ..data.feeds import InMemoryFeedStore
from ..data.storage import StorageBackend
from ..hedge.hedger import Hedger
from ..models.avellaneda_stoikov import AvellanedaStoikovModel, QuoteResult
from ..risk.kill_switch import KillSwitch
from ..risk.limits import RiskLimits
from ..risk.orphan_reaper import OrphanReaper
from ..signals.impact import ImpactEstimator
from ..signals.microstructure import MicrostructureSignals
from ..signals.volatility import VolatilityEstimator


class MetricsRecorder(Protocol):
    def record(
        self,
        symbol: str,
        *,
        inventory: float,
        pnl_realized: float,
        pnl_unrealized: float,
        spread: float,
        fill_rate: float,
    ) -> None:  # pragma: no cover - interface
        ...


@dataclass
class SymbolState:
    inventory: float = 0.0
    inventory_cost: float = 0.0
    pnl_realized: float = 0.0
    last_quote: Optional[QuoteResult] = None
    open_orders: Dict[str, OrderState] = field(default_factory=dict)
    posted_notional_ema: float = 1e-6
    filled_notional_ema: float = 1e-6

    def unrealized(self, mid: float) -> float:
        return self.inventory * mid - self.inventory_cost

    def fill_rate(self) -> float:
        return self.filled_notional_ema / max(self.posted_notional_ema, 1e-6)


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
        symbol_config: SymbolConfig,
        venue: str,
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
        self._venue = venue
        self._symbol = symbol_config.name
        self._state = SymbolState()
        self._running = False
        self._metrics = metrics
        self._kill_switch = kill_switch
        self._logger = logging.getLogger(f"Quoter[{self._symbol}]")
        self._post_only = symbol_config.post_only
        self._lot_size = symbol_config.lot_size
        self._tick_size = symbol_config.tick_size
        self._maker_fee = symbol_config.maker_fee_bps / 10_000.0
        self._taker_fee = symbol_config.taker_fee_bps / 10_000.0
        self._connector.register_symbol(symbol_config.name)

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
                            self._symbol,
                            inventory=self._state.inventory,
                            pnl_realized=self._state.pnl_realized,
                            pnl_unrealized=self._state.unrealized(snapshot.mid),
                            spread=quote.spread,
                            fill_rate=self._state.fill_rate(),
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
        raw_orders = await self._connector.list_open_orders(symbol=self._symbol)
        current_orders: Dict[str, OrderState] = {}
        orders_by_side: Dict[Side, OrderState] = {}
        for state in raw_orders:
            if state.order.order_id is None:
                continue
            current_orders[state.order.order_id] = state
            orders_by_side[state.order.side] = state
        self._state.open_orders = current_orders
        risk_orders = {
            order_id: abs(order_state.order.price * order_state.remaining)
            for order_id, order_state in current_orders.items()
        }
        self._risk.sync_orders(self._symbol, risk_orders)

        desired_prices = {Side.BUY: quote.bid, Side.SELL: quote.ask}
        for side, target_price in desired_prices.items():
            existing = orders_by_side.get(side)
            if existing and abs(existing.order.price - target_price) <= self._tick_size / 2:
                continue
            if existing and existing.order.order_id:
                await self._connector.cancel_order(existing.order.order_id, symbol=self._symbol)
                self._risk.record_cancel(self._symbol)
                self._risk.remove_order(existing.order.order_id, self._symbol)
                self._state.open_orders.pop(existing.order.order_id, None)
            order = Order(
                venue=self._venue,
                symbol=self._symbol,
                side=side,
                price=target_price,
                size=self._lot_size,
                post_only=self._post_only,
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
            state = OrderState(order=order_with_id, remaining=order.size)
            self._state.open_orders[order_id] = state
            self._risk.register_order(order_id, order_with_id)
            notional = abs(order.price * order.size)
            self._state.posted_notional_ema = 0.9 * self._state.posted_notional_ema + 0.1 * notional

    async def _drain_fills(self, snapshot: OrderBookSnapshot) -> None:
        while True:
            fill = await self._connector.poll_fill()
            if fill is None:
                break
            realized = self._apply_fill(fill)
            if fill.fee != 0:
                fee = abs(fill.fee)
            else:
                fee_rate = self._maker_fee if fill.order_id in self._state.open_orders else self._taker_fee
                fee = max(fee_rate, 0.0) * abs(fill.price * fill.size)
            realized -= fee
            self._state.pnl_realized += realized
            self._state.filled_notional_ema = 0.9 * self._state.filled_notional_ema + 0.1 * abs(
                fill.price * fill.size
            )
            self._risk.record_fill(fill, snapshot.mid, realized)
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
            if fill.order_id:
                self._risk.remove_order(fill.order_id, fill.symbol)
                self._state.open_orders.pop(fill.order_id, None)

    def _apply_fill(self, fill: Fill) -> float:
        state = self._state
        inventory_before = state.inventory
        cost_before = state.inventory_cost
        avg_cost = cost_before / inventory_before if abs(inventory_before) > 1e-9 else 0.0
        realized = 0.0
        if fill.side == Side.BUY:
            inventory_after = inventory_before + fill.size
            if inventory_before < 0:
                closing = min(fill.size, abs(inventory_before))
                realized += (avg_cost - fill.price) * closing
                remaining = inventory_after
                if remaining < 0:
                    state.inventory_cost = avg_cost * remaining
                else:
                    residual = fill.size - closing
                    state.inventory_cost = residual * fill.price
            else:
                state.inventory_cost = cost_before + fill.price * fill.size
        else:
            inventory_after = inventory_before - fill.size
            if inventory_before > 0:
                closing = min(fill.size, inventory_before)
                realized += (fill.price - avg_cost) * closing
                remaining = inventory_after
                if remaining > 0:
                    state.inventory_cost = avg_cost * remaining
                else:
                    residual = fill.size - closing
                    state.inventory_cost = -residual * fill.price
            else:
                state.inventory_cost = cost_before - fill.price * fill.size
        state.inventory = inventory_after
        if abs(state.inventory) < 1e-9:
            state.inventory = 0.0
            state.inventory_cost = 0.0
        return realized

    async def _cancel_all(self) -> None:
        orders = await self._connector.list_open_orders(symbol=self._symbol)
        for state in orders:
            if state.order.order_id:
                await self._connector.cancel_order(state.order.order_id, symbol=self._symbol)
                self._risk.remove_order(state.order.order_id, state.order.symbol)
        self._state.open_orders.clear()
