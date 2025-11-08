"""Kill switch utilities."""

from __future__ import annotations

import asyncio
from typing import Awaitable, Callable, Optional


class KillSwitch:
    """Counts error events and triggers a callback when the threshold is breached."""

    def __init__(self, threshold: int, on_trigger: Callable[[str], Awaitable[None]]) -> None:
        if threshold <= 0:
            raise ValueError("threshold must be positive")
        self._threshold = threshold
        self._on_trigger = on_trigger
        self._count = 0
        self._lock = asyncio.Lock()
        self._reason: Optional[str] = None

    @property
    def tripped(self) -> bool:
        return self._reason is not None

    @property
    def reason(self) -> Optional[str]:
        return self._reason

    async def record_error(self, reason: str) -> None:
        async with self._lock:
            if self._reason is not None:
                return
            self._count += 1
            if self._count >= self._threshold:
                self._reason = reason
                await self._on_trigger(reason)
                self._count = 0

    async def reset(self) -> None:
        async with self._lock:
            self._count = 0
            self._reason = None


__all__ = ["KillSwitch"]
