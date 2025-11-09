"""Orphan order reaper."""

from __future__ import annotations

import asyncio
import datetime as dt
from typing import Dict

from ..connectors.cex_ccxt import ExchangeConnector


class OrphanReaper:
    def __init__(self, connector: ExchangeConnector, timeout_seconds: float = 10.0) -> None:
        self._connector = connector
        self._timeout = timeout_seconds
        self._timestamps: Dict[str, dt.datetime] = {}
        self._lock = asyncio.Lock()

    async def track(self, order_id: str) -> None:
        async with self._lock:
            self._timestamps[order_id] = dt.datetime.utcnow()

    async def sweep(self) -> None:
        now = dt.datetime.utcnow()
        async with self._lock:
            stale = [order_id for order_id, ts in self._timestamps.items() if (now - ts).total_seconds() > self._timeout]
        for order_id in stale:
            await self._connector.cancel_order(order_id)
            async with self._lock:
                self._timestamps.pop(order_id, None)
