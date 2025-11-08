"""Short horizon volatility estimation."""

from __future__ import annotations

import collections
import math
from typing import Deque, Dict

from ..core.types import OrderBookSnapshot


class VolatilityEstimator:
    def __init__(self, window: int = 100) -> None:
        self._returns: Dict[str, Deque[float]] = collections.defaultdict(lambda: collections.deque(maxlen=window))
        self._last_mid: Dict[str, float] = {}

    def update(self, snapshot: OrderBookSnapshot) -> float:
        mid = snapshot.mid
        last = self._last_mid.get(snapshot.symbol)
        if last is not None and last > 0:
            ret = (mid - last) / last
            self._returns[snapshot.symbol].append(ret)
        self._last_mid[snapshot.symbol] = mid
        return self.sigma(snapshot.symbol)

    def sigma(self, symbol: str) -> float:
        returns = self._returns.get(symbol)
        if not returns:
            return 0.0
        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / max(len(returns) - 1, 1)
        return math.sqrt(variance)
