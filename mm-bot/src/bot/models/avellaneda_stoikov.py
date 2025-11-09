"""Avellaneda–Stoikov quoting model."""

from __future__ import annotations

import math
from dataclasses import dataclass

from ..core.types import OrderBookSnapshot
from ..core.utils import clamp, snap
from ..signals.microstructure import MicrostructureFeature


@dataclass
class QuoteResult:
    bid: float
    ask: float
    spread: float


class AvellanedaStoikovModel:
    def __init__(self, gamma: float, horizon: float, kappa: float, min_spread: float, skew_alpha: float) -> None:
        self.gamma = gamma
        self.horizon = horizon
        self.kappa = kappa
        self.min_spread = min_spread
        self.skew_alpha = skew_alpha

    def _reservation_price(self, mid: float, inventory: float, sigma: float) -> float:
        return mid - inventory * self.gamma * (sigma**2) * self.horizon

    def _optimal_half_spread(self, sigma: float) -> float:
        return (self.gamma * (sigma**2) * self.horizon) / 2 + (1 / self.kappa) * math.log(1 + self.kappa / self.gamma)

    def generate_quotes(
        self,
        snapshot: OrderBookSnapshot,
        inventory: float,
        sigma: float,
        feature: MicrostructureFeature,
        tick_size: float,
        min_tick_spread: float,
        impact_lambda: float,
    ) -> QuoteResult:
        effective_mid = 0.6 * feature.microprice + 0.4 * snapshot.mid
        reservation = self._reservation_price(effective_mid, inventory, sigma)
        half_spread = max(self._optimal_half_spread(sigma), self.min_spread / 2)
        skew = self.skew_alpha * inventory
        skew += 0.4 * feature.order_flow_imbalance
        skew -= 0.2 * feature.queue_imbalance
        impact_multiplier = 1.0
        if abs(impact_lambda) > 0.01:
            impact_multiplier += clamp(abs(impact_lambda), 0.0, 1.5)
        if sigma > 0.05:
            impact_multiplier += clamp(sigma, 0.0, 1.0)
        half_spread *= impact_multiplier
        bid = reservation - half_spread - skew
        ask = reservation + half_spread + skew
        spread = max(ask - bid, min_tick_spread)
        mid = (bid + ask) / 2
        bid = snap(mid - spread / 2, tick_size)
        ask = snap(mid + spread / 2, tick_size)
        return QuoteResult(bid=bid, ask=ask, spread=max(ask - bid, min_tick_spread))
