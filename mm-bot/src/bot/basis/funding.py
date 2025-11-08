"""Basis and funding capture module."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Dict

from ..core.types import FundingInfo


@dataclass
class FundingPolicy:
    enabled: bool
    max_notional: float
    threshold: float


class FundingBook:
    def __init__(self) -> None:
        self._positions: Dict[str, float] = {}
        self._accrual: Dict[str, float] = {}

    def update(self, symbol: str, position: float, funding_rate: float) -> None:
        self._positions[symbol] = position
        accrual = position * funding_rate
        self._accrual[symbol] = self._accrual.get(symbol, 0.0) + accrual

    def total_accrual(self) -> float:
        return sum(self._accrual.values())


class FundingCapture:
    def __init__(self, policy: FundingPolicy) -> None:
        self._policy = policy
        self._book = FundingBook()

    def on_funding(self, info: FundingInfo, position: float) -> None:
        if not self._policy.enabled:
            return
        if abs(position * info.next_rate) > self._policy.threshold:
            notional = abs(position * info.next_rate)
            if notional <= self._policy.max_notional:
                self._book.update(info.symbol, position, info.next_rate)

    def accrual(self) -> float:
        return self._book.total_accrual()
