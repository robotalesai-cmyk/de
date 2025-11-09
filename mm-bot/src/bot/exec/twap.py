"""Simple TWAP executor."""

from __future__ import annotations

import asyncio
from typing import Awaitable, Callable


class TWAPExecutor:
    def __init__(self, slices: int, interval: float) -> None:
        self._slices = slices
        self._interval = interval

    async def execute(self, submit_slice: Callable[[float], Awaitable[None]], total_size: float) -> None:
        size_per_slice = total_size / self._slices
        for _ in range(self._slices):
            await submit_slice(size_per_slice)
            await asyncio.sleep(self._interval)
