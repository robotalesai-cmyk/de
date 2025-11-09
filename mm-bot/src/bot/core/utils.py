"""Utility helpers."""

from __future__ import annotations

import asyncio
import math
import os
import random
from typing import Iterable, Optional


def snap(value: float, step: float) -> float:
    """Snap a value to the nearest multiple of ``step``."""

    if step <= 0:
        raise ValueError("step must be positive")
    return round(value / step) * step


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


async def jitter_sleep(base: float, jitter: float = 0.1) -> None:
    wait = base + random.uniform(-jitter, jitter)
    await asyncio.sleep(max(wait, 0.0))


def ewma(values: Iterable[float], alpha: float) -> float:
    iterator = iter(values)
    try:
        result = next(iterator)
    except StopIteration as exc:
        raise ValueError("values must not be empty") from exc
    for value in iterator:
        result = alpha * value + (1 - alpha) * result
    return result


def annualized_sharpe(returns: Iterable[float], periods_per_year: int = 365 * 24) -> float:
    values = list(returns)
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((r - mean) ** 2 for r in values) / max(len(values) - 1, 1)
    if variance == 0:
        return 0.0
    return (mean / math.sqrt(variance)) * math.sqrt(periods_per_year)


def load_exchange_credentials(venue: str) -> Optional["ExchangeCredentials"]:
    from .types import ExchangeCredentials  # Local import to avoid circular dependency

    prefix = venue.upper().replace("-", "_")
    api_key = os.getenv(f"{prefix}_API_KEY") or os.getenv("EXCHANGE_API_KEY")
    secret = os.getenv(f"{prefix}_API_SECRET") or os.getenv("EXCHANGE_API_SECRET")
    passphrase = os.getenv(f"{prefix}_API_PASSPHRASE") or os.getenv("EXCHANGE_API_PASSPHRASE")
    if api_key and secret:
        return ExchangeCredentials(api_key=api_key, secret=secret, passphrase=passphrase)
    return None
