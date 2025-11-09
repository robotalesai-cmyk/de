"""Simple VWAP executor."""

from __future__ import annotations

from typing import Callable, Sequence


class VWAPExecutor:
    def __init__(self, profile: Sequence[float]) -> None:
        self._profile = profile

    async def execute(self, submit_slice: Callable[[float], None], total_size: float) -> None:
        remaining = total_size
        for weight in self._profile:
            slice_size = total_size * weight
            submit_slice(slice_size)
            remaining -= slice_size
        if abs(remaining) > 1e-9:
            submit_slice(remaining)
