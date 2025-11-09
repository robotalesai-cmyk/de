"""Smart order routing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from ..connectors.cex_ccxt import ExchangeConnector
from ..core.types import Order


@dataclass
class VenueRoute:
    venue: str
    weight: float


class SmartOrderRouter:
    def __init__(self, connectors: Dict[str, ExchangeConnector]) -> None:
        self._connectors = connectors

    async def execute(self, order: Order) -> str:
        connector = self._connectors.get(order.venue)
        if connector is None:
            raise KeyError(f"No connector for venue {order.venue}")
        return await connector.place_order(order)
