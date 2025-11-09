from __future__ import annotations

import asyncio

from bot.core.types import Order, Side
from bot.risk.kill_switch import KillSwitch
from bot.risk.limits import RiskLimits, SymbolLimits


def test_risk_limits_blocks_excess_inventory() -> None:
    limits = RiskLimits(
        {"BTC": SymbolLimits(max_position=1.0, max_order_notional=1000.0)},
        max_drawdown=100.0,
        max_daily_loss=100.0,
        max_inventory_notional=1000.0,
    )
    limits.update_inventory("BTC", 0.9)
    order = Order(venue="v", symbol="BTC", side=Side.BUY, price=100.0, size=0.2)
    assert not limits.check_order(order)


def test_kill_switch_triggers() -> None:
    triggered: list[str] = []

    async def on_trigger(reason: str) -> None:
        triggered.append(reason)

    ks = KillSwitch(threshold=2, on_trigger=on_trigger)

    asyncio.run(ks.record_error("first"))
    assert triggered == []
    asyncio.run(ks.record_error("second"))
    assert triggered == ["second"]
