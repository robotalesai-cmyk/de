"""Simple async event bus."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, Awaitable, Callable, DefaultDict, List

EventHandler = Callable[[Any], Awaitable[None]]


class EventBus:
    def __init__(self) -> None:
        self._subscribers: DefaultDict[str, List[EventHandler]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def publish(self, topic: str, payload: Any) -> None:
        async with self._lock:
            subscribers = list(self._subscribers.get(topic, []))
        await asyncio.gather(*(handler(payload) for handler in subscribers), return_exceptions=True)

    async def subscribe(self, topic: str, handler: EventHandler) -> None:
        async with self._lock:
            self._subscribers[topic].append(handler)

    async def unsubscribe(self, topic: str, handler: EventHandler) -> None:
        async with self._lock:
            if handler in self._subscribers.get(topic, []):
                self._subscribers[topic].remove(handler)
