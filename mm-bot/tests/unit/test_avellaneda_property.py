import math

import hypothesis.strategies as st
from hypothesis import given

from bot.models.avellaneda_stoikov import AvellanedaStoikovModel
from bot.signals.microstructure import MicrostructureFeature


class DummySnapshot:
    def __init__(self, mid: float) -> None:
        self.mid = mid


@given(
    mid=st.floats(min_value=1000.0, max_value=40000.0),
    inventory=st.floats(min_value=-5.0, max_value=5.0),
    sigma=st.floats(min_value=0.0001, max_value=0.2),
    gamma=st.floats(min_value=0.01, max_value=1.0),
    horizon=st.floats(min_value=1.0, max_value=120.0),
    kappa=st.floats(min_value=0.1, max_value=5.0),
)
def test_quotes_are_well_ordered(mid, inventory, sigma, gamma, horizon, kappa):
    model = AvellanedaStoikovModel(
        gamma=gamma,
        horizon=horizon,
        kappa=kappa,
        min_spread=0.01,
        skew_alpha=0.1,
    )
    feature = MicrostructureFeature(microprice=mid, queue_imbalance=0.0, order_flow_imbalance=0.0)
    snapshot = DummySnapshot(mid=mid)
    quote = model.generate_quotes(
        snapshot=snapshot,  # type: ignore[arg-type]
        inventory=inventory,
        sigma=sigma,
        feature=feature,
        tick_size=0.01,
        min_tick_spread=0.01,
        impact_lambda=0.0,
    )
    assert quote.ask >= quote.bid
    assert quote.spread >= 0.01
    assert not math.isnan(quote.bid) and not math.isnan(quote.ask)
