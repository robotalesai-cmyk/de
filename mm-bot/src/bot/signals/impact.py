"""Kyle's lambda style impact estimator."""

from __future__ import annotations

from typing import Dict

from ..core.types import Trade


class ImpactEstimator:
    def __init__(self, decay: float = 0.99) -> None:
        self._decay = decay
        self._state: Dict[str, tuple[float, float, float]] = {}
        # state: (mean_volume, mean_return, lambda_estimate)

    def update(self, trade: Trade, price_return: float) -> float:
        key = trade.symbol
        mean_vol, mean_ret, lam = self._state.get(key, (0.0, 0.0, 0.0))
        signed_volume = trade.size if trade.side.value == "buy" else -trade.size
        mean_vol = self._decay * mean_vol + (1 - self._decay) * signed_volume
        mean_ret = self._decay * mean_ret + (1 - self._decay) * price_return
        if abs(signed_volume) > 1e-9:
            lam = self._decay * lam + (1 - self._decay) * (price_return / signed_volume)
        self._state[key] = (mean_vol, mean_ret, lam)
        return lam

    def get(self, symbol: str) -> float:
        return self._state.get(symbol, (0.0, 0.0, 0.0))[2]
