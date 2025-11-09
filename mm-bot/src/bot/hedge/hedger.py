"""Inventory hedging logic."""

from __future__ import annotations

from dataclasses import dataclass

from ..connectors.cex_ccxt import ExchangeConnector
from ..core.types import Order, OrderBookSnapshot, Side
from ..exec.twap import TWAPExecutor


@dataclass
class HedgePolicy:
    enabled: bool
    threshold: float
    max_notional: float


class Hedger:
    def __init__(
        self,
        connector: ExchangeConnector,
        policy: HedgePolicy,
        *,
        twap_slices: int = 3,
        twap_interval: float = 0.3,
    ) -> None:
        self._connector = connector
        self._policy = policy
        self.last_notional: float = 0.0
        self._twap = TWAPExecutor(twap_slices, twap_interval)
        self._twap_slices = twap_slices

    async def maybe_hedge(self, snapshot: OrderBookSnapshot, inventory: float, tick_size: float, lot_size: float) -> float:
        self.last_notional = 0.0
        if not self._policy.enabled:
            return inventory
        if abs(inventory) < self._policy.threshold:
            return inventory
        side = Side.SELL if inventory > 0 else Side.BUY
        price = snapshot.bid.price if side == Side.SELL else snapshot.ask.price
        target_size = min(abs(inventory), self._policy.max_notional / max(price, tick_size))
        desired_size = max(target_size, lot_size)
        slices = 1 if desired_size <= self._policy.max_notional / 2 else self._twap_slices
        executed_delta = 0.0

        async def submit(size: float) -> None:
            nonlocal executed_delta
            snapped_size = max(round(size / lot_size) * lot_size, lot_size)
            order = Order(
                venue=snapshot.venue,
                symbol=snapshot.symbol,
                side=side,
                price=price,
                size=snapped_size,
                post_only=False,
            )
            order_id = await self._connector.place_order(order)
            await self._connector.process_cross(snapshot.symbol, snapshot.bid.price, snapshot.ask.price)
            while True:
                fill = await self._connector.poll_fill()
                if fill is None:
                    break
                if fill.order_id != order_id:
                    continue
                delta = fill.size if fill.side == Side.BUY else -fill.size
                executed_delta += delta
                self.last_notional += abs(fill.price * fill.size)

        if slices > 1:
            await self._twap.execute(submit, desired_size)
        else:
            await submit(desired_size)
        return inventory + executed_delta
