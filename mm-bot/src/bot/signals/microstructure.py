"""Microstructure signal extraction."""

from __future__ import annotations

import collections
from dataclasses import dataclass
from typing import Deque, Dict, Optional

from ..core.types import OrderBookSnapshot, Trade


@dataclass
class MicrostructureFeature:
    microprice: float
    queue_imbalance: float
    order_flow_imbalance: float


class MicrostructureSignals:
    def __init__(self, ofi_window: int = 20, ofi_alpha: float = 0.3) -> None:
        self._last_snapshot: Dict[str, OrderBookSnapshot] = {}
        self._ofi_history: Dict[str, Deque[float]] = collections.defaultdict(lambda: collections.deque(maxlen=ofi_window))
        self._ofi_alpha = ofi_alpha

    def update_snapshot(self, snapshot: OrderBookSnapshot) -> MicrostructureFeature:
        microprice = self._compute_microprice(snapshot)
        qi = self._compute_qi(snapshot)
        last = self._last_snapshot.get(snapshot.symbol)
        ofi = self._ofi_history[snapshot.symbol][-1] if self._ofi_history[snapshot.symbol] else 0.0
        if last is not None:
            ofi_delta = self._compute_ofi(last, snapshot)
            self._ofi_history[snapshot.symbol].append(ofi_delta)
            ofi = self._ewma(self._ofi_history[snapshot.symbol])
        self._last_snapshot[snapshot.symbol] = snapshot
        return MicrostructureFeature(microprice=microprice, queue_imbalance=qi, order_flow_imbalance=ofi)

    def update_trade(self, trade: Trade) -> None:
        # Could be extended to incorporate trade imbalance; for now store placeholder.
        history = self._ofi_history[trade.symbol]
        signed_size = trade.size if trade.side.value == "buy" else -trade.size
        history.append(signed_size)

    def get(self, symbol: str) -> Optional[MicrostructureFeature]:
        snapshot = self._last_snapshot.get(symbol)
        if snapshot is None:
            return None
        microprice = self._compute_microprice(snapshot)
        qi = self._compute_qi(snapshot)
        ofi = self._ewma(self._ofi_history[symbol]) if self._ofi_history[symbol] else 0.0
        return MicrostructureFeature(microprice=microprice, queue_imbalance=qi, order_flow_imbalance=ofi)

    def _compute_microprice(self, snapshot: OrderBookSnapshot) -> float:
        bid_contrib = snapshot.ask.price * snapshot.bid.size
        ask_contrib = snapshot.bid.price * snapshot.ask.size
        denom = snapshot.bid.size + snapshot.ask.size
        if denom == 0:
            return snapshot.mid
        return (bid_contrib + ask_contrib) / denom

    def _compute_qi(self, snapshot: OrderBookSnapshot) -> float:
        denom = snapshot.bid.size + snapshot.ask.size
        if denom == 0:
            return 0.0
        return (snapshot.bid.size - snapshot.ask.size) / denom

    def _compute_ofi(self, last: OrderBookSnapshot, current: OrderBookSnapshot) -> float:
        bid_delta = current.bid.size - last.bid.size
        ask_delta = current.ask.size - last.ask.size
        price_move = current.mid - last.mid
        return bid_delta - ask_delta + price_move

    def _ewma(self, values: Deque[float]) -> float:
        weight = 0.0
        result = 0.0
        alpha = self._ofi_alpha
        for value in reversed(values):
            result = alpha * value + (1 - alpha) * result
            weight = alpha + (1 - alpha) * weight
        return result if weight else 0.0
