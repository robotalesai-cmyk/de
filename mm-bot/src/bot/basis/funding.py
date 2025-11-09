"""Basis and funding capture module."""

from __future__ import annotations

import collections
from dataclasses import dataclass
from typing import Deque, Dict

from ..core.types import FundingInfo, OrderBookSnapshot


@dataclass
class FundingPolicy:
    enabled: bool
    max_notional: float
    target_notional: float
    threshold: float


class FundingCapture:
    """Lightweight basis/funding capture overlay."""

    def __init__(self, policy: FundingPolicy) -> None:
        self._policy = policy
        self._spot_mid: Dict[str, float] = {}
        self._perp_mark: Dict[str, float] = {}
        self._funding_rates: Dict[str, float] = {}
        self._basis_history: Dict[str, Deque[float]] = collections.defaultdict(lambda: collections.deque(maxlen=100))
        self._positions: Dict[str, float] = {}
        self._accrual: float = 0.0

    def observe_snapshot(self, symbol: str, snapshot: OrderBookSnapshot, is_perp: bool) -> None:
        base = self._base_symbol(symbol)
        if is_perp:
            self._perp_mark[base] = snapshot.mark_price or snapshot.mid
        else:
            self._spot_mid[base] = snapshot.mid
        self._update_basis(base)

    def observe_funding(self, info: FundingInfo) -> None:
        base = self._base_symbol(info.symbol)
        self._funding_rates[base] = info.next_rate
        position = self._positions.get(base, 0.0)
        if position != 0.0:
            accrual = position * info.next_rate
            self._accrual += accrual

    def position(self, base: str) -> float:
        return self._positions.get(base, 0.0)

    def accrual(self) -> float:
        return self._accrual

    def snapshot(self) -> Dict[str, float]:
        return dict(self._positions)

    def _update_basis(self, base: str) -> None:
        if not self._policy.enabled:
            return
        spot = self._spot_mid.get(base)
        perp = self._perp_mark.get(base)
        if spot is None or perp is None:
            return
        basis = perp - spot
        history = self._basis_history[base]
        history.append(basis)
        predicted = sum(history) / len(history)
        funding_rate = self._funding_rates.get(base, 0.0)
        signal = predicted + funding_rate * spot
        desired_notional = 0.0
        if abs(signal) >= self._policy.threshold:
            direction = 1.0 if signal > 0 else -1.0
            desired_notional = direction * min(self._policy.target_notional, self._policy.max_notional)
        self._positions[base] = desired_notional

    def _base_symbol(self, symbol: str) -> str:
        return symbol.split("-")[0]
