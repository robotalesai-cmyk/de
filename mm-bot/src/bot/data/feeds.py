"""Market data feeds for synthetic and Kucoin venues."""

from __future__ import annotations

import asyncio
import contextlib
import datetime as dt
import logging
import random
from typing import Any, Dict, Optional

try:  # pragma: no cover - optional dependency in tests
    import orjson
except ModuleNotFoundError:  # pragma: no cover - fallback to stdlib json
    import json as _json

    class _OrjsonModule:
        @staticmethod
        def loads(data: str) -> Any:
            return _json.loads(data)

        @staticmethod
        def dumps(obj: Any) -> bytes:
            return _json.dumps(obj).encode()

    orjson = _OrjsonModule()  # type: ignore
try:  # pragma: no cover - optional dependency in tests
    import websockets
except ModuleNotFoundError:  # pragma: no cover - optional dependency missing
    websockets = None  # type: ignore

try:  # pragma: no cover - optional dependency in tests
    import ccxt.async_support as ccxt_async  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - optional dependency missing
    ccxt_async = None  # type: ignore

from ..core.events import EventBus
from ..core.types import OrderBookLevel, OrderBookSnapshot, Side, Trade

SNAPSHOT_TOPIC = "snapshot"
TRADE_TOPIC = "trade"


class InMemoryFeedStore:
    """Keeps latest snapshots and trades in memory."""

    def __init__(self) -> None:
        self.snapshots: Dict[str, OrderBookSnapshot] = {}
        self._lock = asyncio.Lock()

    async def update_snapshot(self, snapshot: OrderBookSnapshot) -> None:
        async with self._lock:
            self.snapshots[snapshot.symbol] = snapshot

    async def get_snapshot(self, symbol: str) -> Optional[OrderBookSnapshot]:
        async with self._lock:
            return self.snapshots.get(symbol)


class SyntheticFeed:
    """Simple synthetic feed for paper/backtest operation."""

    def __init__(self, event_bus: EventBus, venue: str, symbol: str, base_price: float) -> None:
        self._bus = event_bus
        self._venue = venue
        self._symbol = symbol
        self._base_price = base_price
        self._running = False

    async def run(self, store: InMemoryFeedStore) -> None:
        self._running = True
        mid = self._base_price
        while self._running:
            drift = random.uniform(-1, 1)
            mid = max(mid + drift, 1.0)
            spread = max(0.5, abs(drift))
            bid = mid - spread / 2
            ask = mid + spread / 2
            bid_size = random.uniform(0.1, 0.5)
            ask_size = random.uniform(0.1, 0.5)
            snapshot = OrderBookSnapshot(
                venue=self._venue,
                symbol=self._symbol,
                timestamp=dt.datetime.utcnow(),
                bid=OrderBookLevel(price=bid, size=bid_size),
                ask=OrderBookLevel(price=ask, size=ask_size),
                last_trade_price=mid,
                last_trade_size=random.uniform(0.01, 0.1),
                mark_price=mid,
            )
            await store.update_snapshot(snapshot)
            await self._bus.publish(SNAPSHOT_TOPIC, snapshot)
            trade = Trade(
                venue=self._venue,
                symbol=self._symbol,
                timestamp=dt.datetime.utcnow(),
                price=mid + random.uniform(-spread / 2, spread / 2),
                size=random.uniform(0.01, 0.2),
                side=random.choice([Side.BUY, Side.SELL]),
            )
            await self._bus.publish(TRADE_TOPIC, trade)
            await asyncio.sleep(0.5)

    def stop(self) -> None:
        self._running = False


class KucoinFeed:
    """Stream best bid/ask and trades from Kucoin public websocket."""

    def __init__(
        self,
        event_bus: EventBus,
        venue: str,
        symbol: str,
        subscription_symbol: Optional[str] = None,
    ) -> None:
        self._bus = event_bus
        self._venue = venue
        self._symbol = symbol
        self._subscription = subscription_symbol or symbol
        self._running = False
        self._log = logging.getLogger(f"KucoinFeed[{symbol}]")

    async def run(self, store: InMemoryFeedStore) -> None:
        self._running = True
        backoff = 1.0
        while self._running:
            try:
                await self._stream(store)
                backoff = 1.0
            except asyncio.CancelledError:  # pragma: no cover - cooperative cancellation
                raise
            except Exception as exc:  # pragma: no cover - network errors
                self._log.exception("feed error: %s", exc)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30.0)

    async def _stream(self, store: InMemoryFeedStore) -> None:
        if websockets is None:
            raise RuntimeError("websockets is required for live Kucoin feeds")
        token_payload = await self._fetch_bullet_token()
        instance = token_payload["instanceServers"][0]
        token = token_payload["token"]
        endpoint = instance["endpoint"].rstrip("/")
        ping_interval = float(instance.get("pingInterval", 20000)) / 1000.0
        url = f"{endpoint}?token={token}"
        async with websockets.connect(url, ping_interval=None, ping_timeout=None) as ws:
            await self._subscribe(ws)
            ping_task = asyncio.create_task(self._ping(ws, ping_interval))
            try:
                while self._running:
                    raw = await ws.recv()
                    message = orjson.loads(raw)
                    msg_type = message.get("type")
                    if msg_type in {"welcome", "ack"}:
                        continue
                    if msg_type == "pong":
                        continue
                    if msg_type == "ping":
                        payload = {"type": "pong", "id": message.get("id")}
                        await ws.send(orjson.dumps(payload).decode())
                        continue
                    if msg_type == "error":
                        raise RuntimeError(f"Kucoin feed error: {message}")
                    if msg_type == "message":
                        await self._handle_message(message, store)
            finally:
                ping_task.cancel()
                with contextlib.suppress(Exception):
                    await ping_task

    async def _subscribe(self, ws: "websockets.WebSocketClientProtocol") -> None:
        topics = [
            f"/market/ticker:{self._subscription}",
            f"/market/match:{self._subscription}",
        ]
        for topic in topics:
            payload = {
                "id": str(random.randint(1, 10_000_000)),
                "type": "subscribe",
                "topic": topic,
                "privateChannel": False,
                "response": True,
            }
            await ws.send(orjson.dumps(payload).decode())

    async def _ping(self, ws: "websockets.WebSocketClientProtocol", interval: float) -> None:
        try:
            while self._running:
                await asyncio.sleep(interval)
                payload = {"type": "ping", "id": str(random.randint(1, 10_000_000))}
                await ws.send(orjson.dumps(payload).decode())
        except asyncio.CancelledError:  # pragma: no cover - cooperative cancellation
            raise

    async def _handle_message(self, message: Dict[str, Any], store: InMemoryFeedStore) -> None:
        topic = message.get("topic", "")
        data = message.get("data", {})
        if topic.startswith("/market/ticker"):
            snapshot = self._snapshot_from_ticker(data)
            if snapshot:
                await store.update_snapshot(snapshot)
                await self._bus.publish(SNAPSHOT_TOPIC, snapshot)
        elif topic.startswith("/market/match"):
            trade = self._trade_from_match(data)
            if trade:
                await self._bus.publish(TRADE_TOPIC, trade)

    async def _fetch_bullet_token(self) -> Dict[str, Any]:
        if ccxt_async is None:
            raise RuntimeError("ccxt is required for live Kucoin feeds")
        exchange = ccxt_async.kucoin({"enableRateLimit": True})
        try:
            response = await exchange.public_get_bullet_public()
            return response["data"]
        finally:
            await exchange.close()

    def _snapshot_from_ticker(self, data: Dict[str, Any]) -> Optional[OrderBookSnapshot]:
        try:
            bid = float(data.get("bestBid", 0.0))
            ask = float(data.get("bestAsk", 0.0))
            bid_size = float(data.get("bestBidSize", 0.0))
            ask_size = float(data.get("bestAskSize", 0.0))
            last_price = float(data.get("price", data.get("lastTradedPrice", 0.0)))
            last_size = float(data.get("lastTradedSize", 0.0))
        except (TypeError, ValueError):  # pragma: no cover - defensive
            self._log.warning("invalid ticker payload: %s", data)
            return None
        ts_value = data.get("time")
        timestamp = dt.datetime.utcnow()
        if isinstance(ts_value, (int, float)):
            # Kucoin timestamps are in nanoseconds
            timestamp = dt.datetime.fromtimestamp(ts_value / 1_000_000_000, tz=dt.timezone.utc)
        snapshot = OrderBookSnapshot(
            venue=self._venue,
            symbol=self._symbol,
            timestamp=timestamp.replace(tzinfo=None),
            bid=OrderBookLevel(price=bid, size=bid_size),
            ask=OrderBookLevel(price=ask, size=ask_size),
            last_trade_price=last_price or (bid + ask) / 2,
            last_trade_size=last_size if last_size > 0 else max(bid_size, ask_size),
            mark_price=float(data.get("markPrice", last_price or (bid + ask) / 2)),
        )
        return snapshot

    def _trade_from_match(self, data: Dict[str, Any]) -> Optional[Trade]:
        try:
            price = float(data.get("price"))
            size = float(data.get("size"))
            side = Side(data.get("side", "buy"))
        except (TypeError, ValueError, KeyError):  # pragma: no cover - defensive
            self._log.debug("invalid trade payload: %s", data)
            return None
        ts_value = data.get("time")
        timestamp = dt.datetime.utcnow()
        if isinstance(ts_value, (int, float)):
            timestamp = dt.datetime.fromtimestamp(ts_value / 1_000_000_000, tz=dt.timezone.utc)
        return Trade(
            venue=self._venue,
            symbol=self._symbol,
            timestamp=timestamp.replace(tzinfo=None),
            price=price,
            size=size,
            side=side,
        )

    def stop(self) -> None:
        self._running = False
