"""Comprehensive risk limit evaluation."""

from __future__ import annotations

import datetime as dt
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, Optional

from ..core.types import Fill, Order, Side


@dataclass(slots=True)
class SymbolLimits:
    max_position: float
    max_order_notional: float
    account_notional_cap: float
    max_orders: int
    max_cancels_per_minute: Optional[int] = None


@dataclass(slots=True)
class RiskState:
    inventory: Dict[str, float] = field(default_factory=dict)
    mid_prices: Dict[str, float] = field(default_factory=dict)
    realized_pnl: float = 0.0
    peak_equity: float = 0.0
    cancel_events: Dict[str, Deque[dt.datetime]] = field(default_factory=dict)
    halted_reason: Optional[str] = None
    open_orders: Dict[str, Dict[str, float]] = field(default_factory=dict)


class RiskLimits:
    """Evaluate soft and hard limits for trading and hedging."""

    def __init__(
        self,
        limits: Dict[str, SymbolLimits],
        *,
        max_drawdown: float,
        max_daily_loss: float,
        max_inventory_notional: float,
        max_open_orders: int,
    ) -> None:
        self._limits = limits
        self._state = RiskState(
            inventory={symbol: 0.0 for symbol in limits},
            mid_prices={symbol: 0.0 for symbol in limits},
            cancel_events={symbol: deque(maxlen=1000) for symbol in limits},
            open_orders={symbol: {} for symbol in limits},
        )
        self._max_drawdown = max_drawdown
        self._max_daily_loss = max_daily_loss
        self._max_inventory_notional = max_inventory_notional
        self._max_open_orders = max_open_orders

    @property
    def halted(self) -> bool:
        return self._state.halted_reason is not None

    @property
    def halted_reason(self) -> Optional[str]:
        return self._state.halted_reason

    def update_mid(self, symbol: str, mid: float) -> None:
        self._state.mid_prices[symbol] = mid
        self._evaluate_inventory_notional()

    def update_inventory(self, symbol: str, quantity: float) -> None:
        self._state.inventory[symbol] = quantity
        self._evaluate_inventory_notional()

    def check_order(self, order: Order) -> bool:
        if self.halted:
            return False
        limits = self._limits[order.symbol]
        projected = self._state.inventory[order.symbol] + (
            order.size if order.side == Side.BUY else -order.size
        )
        if abs(projected) > limits.max_position:
            return False
        notional = abs(order.price * order.size)
        if notional > limits.max_order_notional:
            return False
        if not self._can_add_order(order.symbol, notional):
            return False
        if limits.max_cancels_per_minute is not None:
            cancels = self._state.cancel_events[order.symbol]
            now = dt.datetime.utcnow()
            while cancels and (now - cancels[0]).total_seconds() > 60:
                cancels.popleft()
            if len(cancels) >= limits.max_cancels_per_minute:
                self._halt(f"cancel rate limit reached for {order.symbol}")
                return False
        return True

    def record_cancel(self, symbol: str) -> None:
        events = self._state.cancel_events[symbol]
        events.append(dt.datetime.utcnow())

    def record_fill(self, fill: Fill, mid_price: float, pnl_delta: float) -> None:
        if self.halted:
            return
        delta = fill.size if fill.side == Side.BUY else -fill.size
        self._state.inventory[fill.symbol] = self._state.inventory.get(fill.symbol, 0.0) + delta
        self._state.mid_prices[fill.symbol] = mid_price
        self._state.realized_pnl += pnl_delta
        if self._state.realized_pnl > self._state.peak_equity:
            self._state.peak_equity = self._state.realized_pnl
        drawdown = self._state.peak_equity - self._state.realized_pnl
        if drawdown > self._max_drawdown:
            self._halt(f"drawdown {drawdown:.2f} exceeds {self._max_drawdown}")
        if -self._state.realized_pnl > self._max_daily_loss:
            self._halt(f"daily loss {self._state.realized_pnl:.2f} below -{self._max_daily_loss}")
        self._evaluate_inventory_notional()

    def _evaluate_inventory_notional(self) -> None:
        total_notional = 0.0
        for symbol, quantity in self._state.inventory.items():
            mid = self._state.mid_prices.get(symbol, 0.0)
            total_notional += abs(quantity * mid)
        if total_notional > self._max_inventory_notional:
            self._halt(
                f"inventory notional {total_notional:.2f} exceeds {self._max_inventory_notional}"
            )

    def _halt(self, reason: str) -> None:
        if self._state.halted_reason is None:
            self._state.halted_reason = reason

    def _can_add_order(self, symbol: str, notional: float) -> bool:
        limits = self._limits[symbol]
        open_orders = self._state.open_orders[symbol]
        if len(open_orders) >= limits.max_orders:
            return False
        total_open = sum(len(orders) for orders in self._state.open_orders.values())
        if total_open >= self._max_open_orders:
            return False
        mid = self._state.mid_prices.get(symbol, 0.0)
        exposure = abs(self._state.inventory[symbol] * mid)
        exposure += sum(open_orders.values()) + notional
        if exposure > limits.account_notional_cap:
            return False
        return True

    def register_order(self, order_id: str, order: Order) -> None:
        notional = abs(order.price * order.size)
        self._state.open_orders[order.symbol][order_id] = notional

    def update_order_notional(self, order_id: str, symbol: str, remaining: float, price: float) -> None:
        orders = self._state.open_orders.get(symbol, {})
        if order_id in orders:
            orders[order_id] = abs(remaining * price)

    def remove_order(self, order_id: str, symbol: str) -> None:
        self._state.open_orders.get(symbol, {}).pop(order_id, None)

    def sync_orders(self, symbol: str, orders: Dict[str, float]) -> None:
        self._state.open_orders[symbol] = dict(orders)


__all__ = ["RiskLimits", "SymbolLimits"]
