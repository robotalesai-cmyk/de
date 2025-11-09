from __future__ import annotations

import datetime as dt

from bot.core.types import OrderBookLevel, OrderBookSnapshot, Side, Trade
from bot.signals.microstructure import MicrostructureSignals


def make_snapshot(bid_price: float, ask_price: float, bid_size: float, ask_size: float) -> OrderBookSnapshot:
    return OrderBookSnapshot(
        venue="test",
        symbol="BTC-PERP",
        timestamp=dt.datetime.utcnow(),
        bid=OrderBookLevel(price=bid_price, size=bid_size),
        ask=OrderBookLevel(price=ask_price, size=ask_size),
        last_trade_price=(bid_price + ask_price) / 2,
        last_trade_size=1.0,
        mark_price=(bid_price + ask_price) / 2,
    )


def test_microprice_and_qi() -> None:
    signals = MicrostructureSignals()
    snapshot = make_snapshot(100.0, 101.0, 2.0, 1.0)
    feature = signals.update_snapshot(snapshot)
    assert feature.microprice > snapshot.mid
    assert feature.queue_imbalance > 0


def test_order_flow_updates_with_trades() -> None:
    signals = MicrostructureSignals()
    snapshot = make_snapshot(100.0, 100.5, 1.0, 1.0)
    signals.update_snapshot(snapshot)
    trade = Trade(
        venue="test",
        symbol="BTC-PERP",
        timestamp=dt.datetime.utcnow(),
        price=100.25,
        size=0.5,
        side=Side.BUY,
    )
    signals.update_trade(trade)
    feature = signals.get("BTC-PERP")
    assert feature is not None
