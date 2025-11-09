"""Stub interfaces for DEX perp connectors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class PerpOrder:
    market: str
    size: float
    price: float
    reduce_only: bool = False


class DEXConnector(Protocol):
    async def place_order(self, order: PerpOrder) -> str:  # pragma: no cover - interface
        ...

    async def cancel_order(self, order_id: str) -> None:  # pragma: no cover - interface
        ...


class NullDexConnector:
    """A do-nothing connector representing unsupported venues."""

    async def place_order(self, order: PerpOrder) -> str:
        raise NotImplementedError("DEX trading not yet implemented")

    async def cancel_order(self, order_id: str) -> None:
        raise NotImplementedError("DEX trading not yet implemented")
