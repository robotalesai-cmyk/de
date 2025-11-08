"""Core datatypes used across the bot."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Dict, Optional


class Side(str, Enum):
    BUY = "buy"
    SELL = "sell"

    @property
    def opposite(self) -> "Side":
        return Side.SELL if self is Side.BUY else Side.BUY


@dataclass(slots=True)
class OrderBookLevel:
    price: float
    size: float


@dataclass(slots=True)
class OrderBookSnapshot:
    venue: str
    symbol: str
    timestamp: dt.datetime
    bid: OrderBookLevel
    ask: OrderBookLevel
    last_trade_price: float
    last_trade_size: float
    mark_price: Optional[float] = None

    @property
    def mid(self) -> float:
        return (self.bid.price + self.ask.price) / 2


@dataclass(slots=True)
class Trade:
    venue: str
    symbol: str
    timestamp: dt.datetime
    price: float
    size: float
    side: Side


@dataclass(slots=True)
class Order:
    venue: str
    symbol: str
    side: Side
    price: float
    size: float
    order_id: Optional[str] = None
    post_only: bool = True


@dataclass(slots=True)
class OrderStatus:
    """Normalized view of an order returned by venue connectors."""

    order_id: str
    symbol: str
    side: Side
    price: float
    size: float
    remaining: float
    status: str


@dataclass(slots=True)
class ExchangeCredentials:
    """Container for API credentials supplied via environment variables."""

    api_key: str
    secret: str
    passphrase: Optional[str] = None


@dataclass(slots=True)
class Fill:
    order_id: str
    venue: str
    symbol: str
    side: Side
    price: float
    size: float
    fee: float
    timestamp: dt.datetime


@dataclass(slots=True)
class Position:
    symbol: str
    quantity: float
    avg_price: float


@dataclass(slots=True)
class FundingInfo:
    venue: str
    symbol: str
    next_rate: float
    next_timestamp: dt.datetime


@dataclass(slots=True)
class MetricsSnapshot:
    timestamp: dt.datetime
    pnl_realized: float
    pnl_unrealized: float
    inventory: Dict[str, float]
    spread_target: float
    fill_rate: float
    hedge_notional: float
    funding_accrual: float
    error_rate: float
