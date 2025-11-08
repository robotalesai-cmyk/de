from __future__ import annotations

from bot.models.avellaneda_stoikov import AvellanedaStoikovModel
from bot.signals.microstructure import MicrostructureFeature


class DummySnapshot:
    def __init__(self, mid: float) -> None:
        self.mid = mid


def test_reservation_price_moves_with_inventory() -> None:
    model = AvellanedaStoikovModel(gamma=0.1, horizon=10, kappa=1.0, min_spread=0.01, skew_alpha=0.0)
    feature = MicrostructureFeature(microprice=100.0, queue_imbalance=0.0, order_flow_imbalance=0.0)
    snap = DummySnapshot(mid=100.0)
    quote_long = model.generate_quotes(snap, inventory=1.0, sigma=0.5, feature=feature, tick_size=0.01, min_tick_spread=0.01, impact_lambda=0.0)
    quote_short = model.generate_quotes(snap, inventory=-1.0, sigma=0.5, feature=feature, tick_size=0.01, min_tick_spread=0.01, impact_lambda=0.0)
    assert quote_long.bid < quote_short.bid
    assert quote_long.ask < quote_short.ask


def test_spread_increases_with_volatility() -> None:
    model = AvellanedaStoikovModel(gamma=0.1, horizon=10, kappa=1.0, min_spread=0.01, skew_alpha=0.0)
    feature = MicrostructureFeature(microprice=100.0, queue_imbalance=0.0, order_flow_imbalance=0.0)
    snap = DummySnapshot(mid=100.0)
    low_vol = model.generate_quotes(snap, inventory=0.0, sigma=0.1, feature=feature, tick_size=0.01, min_tick_spread=0.01, impact_lambda=0.0)
    high_vol = model.generate_quotes(snap, inventory=0.0, sigma=0.5, feature=feature, tick_size=0.01, min_tick_spread=0.01, impact_lambda=0.0)
    assert high_vol.spread >= low_vol.spread
