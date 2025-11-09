"""Async CCXT connector with optional in-memory paper exchange."""

from __future__ import annotations

import asyncio
import contextlib
import datetime as dt
import itertools
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Set

try:  # pragma: no cover - optional dependency for tests
    import ccxt.async_support as ccxt_async  # type: ignore
    from ccxt.base.errors import ExchangeError, NetworkError, RateLimitExceeded
except ModuleNotFoundError:  # pragma: no cover - optional dependency missing
    ccxt_async = None  # type: ignore
    ExchangeError = NetworkError = RateLimitExceeded = Exception  # type: ignore
try:  # pragma: no cover - optional dependency for tests
    from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter
except ModuleNotFoundError:  # pragma: no cover - fallback when tenacity unavailable
    class AsyncRetrying:  # type: ignore[override]
        def __init__(self, *args, **kwargs) -> None:  # pragma: no cover - trivial fallback
            pass

        async def __aiter__(self):  # pragma: no cover - trivial fallback
            class _Attempt:
                def __enter__(self_inner) -> None:
                    return None

                def __exit__(self_inner, exc_type, exc, tb) -> bool:
                    return False

            yield _Attempt()

    def retry_if_exception_type(*args, **kwargs):  # type: ignore[override]
        return None

    def stop_after_attempt(*args, **kwargs):  # type: ignore[override]
        return None

    def wait_exponential_jitter(*args, **kwargs):  # type: ignore[override]
        return None

from ..core.types import ExchangeCredentials, Fill, Order, OrderStatus, Side

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ccxt.async_support.base.exchange import Exchange as CCXTExchange
else:  # pragma: no cover - fallback for runtime without ccxt
    CCXTExchange = object

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class OrderState:
    order: Order
    remaining: float
    status: str = "open"


class PaperExchange:
    """Simple in-memory exchange used for paper trading and tests."""

    def __init__(self, fee_rate: float = 0.0004) -> None:
        self._orders: Dict[str, OrderState] = {}
        self._order_id = itertools.count(1)
        self._lock = asyncio.Lock()
        self._fills: asyncio.Queue[Fill] = asyncio.Queue()
        self._fee_rate = fee_rate

    async def place_order(self, order: Order) -> str:
        order_id = f"paper-{next(self._order_id)}"
        new_order = Order(**{**order.__dict__, "order_id": order_id})
        async with self._lock:
            self._orders[order_id] = OrderState(order=new_order, remaining=new_order.size)
        return order_id

    async def cancel_order(self, order_id: str) -> None:
        async with self._lock:
            self._orders.pop(order_id, None)

    async def list_orders(self, symbol: Optional[str] = None) -> List[OrderState]:
        async with self._lock:
            states = list(self._orders.values())
        if symbol is None:
            return states
        return [state for state in states if state.order.symbol == symbol]

    async def process_cross(self, symbol: str, bid: float, ask: float) -> None:
        async with self._lock:
            orders = list(self._orders.values())
        for state in orders:
            order = state.order
            if order.symbol != symbol:
                continue
            if state.remaining <= 0:
                continue
            filled = False
            price = order.price
            if order.side == Side.BUY and order.price >= ask:
                price = min(order.price, ask)
                filled = True
            elif order.side == Side.SELL and order.price <= bid:
                price = max(order.price, bid)
                filled = True
            if filled:
                await self._register_fill(state, price, state.remaining)

    async def _register_fill(self, state: OrderState, price: float, size: float) -> None:
        async with self._lock:
            order_id = state.order.order_id
            if order_id is None:
                return
            state.remaining = max(state.remaining - size, 0.0)
            if state.remaining == 0.0:
                state.status = "filled"
                self._orders.pop(order_id, None)
        fee = abs(price * size) * self._fee_rate
        fill = Fill(
            order_id=order_id,
            venue=state.order.venue,
            symbol=state.order.symbol,
            side=state.order.side,
            price=price,
            size=size,
            fee=fee,
            timestamp=dt.datetime.utcnow(),
        )
        await self._fills.put(fill)

    async def poll_fills(self) -> Optional[Fill]:
        try:
            return self._fills.get_nowait()
        except asyncio.QueueEmpty:
            return None


class ExchangeConnector:
    """Facade for CCXT venues with background fill polling."""

    def __init__(
        self,
        venue: str,
        *,
        paper: bool = True,
        credentials: Optional[ExchangeCredentials] = None,
        sandbox: bool = False,
        fee_rate: float = 0.0004,
        fill_poll_interval: float = 1.0,
    ) -> None:
        self._venue = venue
        self._paper_exchange = PaperExchange(fee_rate=fee_rate) if paper else None
        self._credentials = credentials
        self._sandbox = sandbox
        self._fill_poll_interval = fill_poll_interval
        self._exchange: Optional[CCXTExchange] = None
        self._fills: asyncio.Queue[Fill] = asyncio.Queue()
        self._symbols: Set[str] = set()
        self._fills_task: Optional[asyncio.Task[None]] = None
        self._seen_trade_ids: Set[str] = set()
        self._last_trade_since: Dict[str, Optional[int]] = {}
        self._lock = asyncio.Lock()

    @property
    def paper(self) -> bool:
        return self._paper_exchange is not None

    def register_symbol(self, symbol: str) -> None:
        self._symbols.add(symbol)

    async def start(self) -> None:
        if self.paper:
            return
        if ccxt_async is None:
            raise RuntimeError("ccxt is required for live trading connectors")
        try:
            exchange_cls = getattr(ccxt_async, self._venue)
        except AttributeError as exc:  # pragma: no cover - defensive
            raise ValueError(f"Unsupported venue for CCXT: {self._venue}") from exc
        params = {"enableRateLimit": True, "timeout": 15000}
        exchange = exchange_cls(params)
        if self._credentials:
            exchange.apiKey = self._credentials.api_key
            exchange.secret = self._credentials.secret
            if self._credentials.passphrase:
                exchange.password = self._credentials.passphrase
        if self._sandbox and hasattr(exchange, "set_sandbox_mode"):
            exchange.set_sandbox_mode(True)
        await exchange.load_markets()
        self._exchange = exchange
        self._fills_task = asyncio.create_task(self._poll_fills())

    async def close(self) -> None:
        if self._fills_task is not None:
            self._fills_task.cancel()
            with contextlib.suppress(Exception):
                await self._fills_task
        if self._exchange is not None:
            with contextlib.suppress(Exception):
                await self._exchange.close()

    async def place_order(self, order: Order) -> str:
        if self._paper_exchange:
            return await self._paper_exchange.place_order(order)
        exchange = self._require_exchange()
        params = {"postOnly": order.post_only}
        result = await self._call(exchange.create_order, order.symbol, "limit", order.side.value, order.size, order.price, params)
        order_id = str(result.get("id") or result.get("orderId"))
        if not order_id:
            raise ExchangeError("Exchange did not return an order id")
        return order_id

    async def cancel_order(self, order_id: str, symbol: Optional[str] = None) -> None:
        if self._paper_exchange:
            await self._paper_exchange.cancel_order(order_id)
            return
        exchange = self._require_exchange()
        await self._call(exchange.cancel_order, order_id, symbol)

    async def cancel_all(self, symbol: Optional[str] = None) -> None:
        states = await self.list_open_orders(symbol)
        for state in states:
            if state.order.order_id:
                await self.cancel_order(state.order.order_id, symbol=state.order.symbol)

    async def list_open_orders(self, symbol: Optional[str] = None) -> List[OrderState]:
        if self._paper_exchange:
            return await self._paper_exchange.list_orders(symbol)
        exchange = self._require_exchange()
        raw_orders = await self._call(exchange.fetch_open_orders, symbol)
        states: List[OrderState] = []
        for raw in raw_orders:
            order_id = str(raw.get("id") or raw.get("orderId"))
            price = float(raw.get("price") or 0.0)
            amount = float(raw.get("amount") or raw.get("size") or 0.0)
            filled = float(raw.get("filled") or raw.get("filledAmount") or 0.0)
            remaining = max(amount - filled, 0.0)
            order = Order(
                venue=self._venue,
                symbol=str(raw.get("symbol") or symbol or ""),
                side=Side(str(raw.get("side"))),
                price=price,
                size=amount,
                order_id=order_id,
                post_only=bool(raw.get("postOnly", True)),
            )
            states.append(OrderState(order=order, remaining=remaining, status=str(raw.get("status", "open"))))
        return states

    async def process_cross(self, symbol: str, bid: float, ask: float) -> None:
        if self._paper_exchange:
            await self._paper_exchange.process_cross(symbol, bid, ask)

    async def poll_fill(self) -> Optional[Fill]:
        if self._paper_exchange:
            return await self._paper_exchange.poll_fills()
        try:
            return self._fills.get_nowait()
        except asyncio.QueueEmpty:
            return None

    async def _poll_fills(self) -> None:
        assert self._exchange is not None
        while True:
            try:
                for symbol in list(self._symbols):
                    since = self._last_trade_since.get(symbol)
                    trades = await self._call(self._exchange.fetch_my_trades, symbol, since)
                    for trade in trades:
                        trade_id = str(trade.get("id"))
                        if not trade_id or trade_id in self._seen_trade_ids:
                            continue
                        self._seen_trade_ids.add(trade_id)
                        timestamp = trade.get("timestamp")
                        ts = dt.datetime.utcnow() if timestamp is None else dt.datetime.utcfromtimestamp(timestamp / 1000)
                        fee_cost = 0.0
                        fee_info = trade.get("fee")
                        if isinstance(fee_info, dict):
                            fee_cost = float(fee_info.get("cost") or 0.0)
                        fill = Fill(
                            order_id=str(trade.get("order") or trade_id),
                            venue=self._venue,
                            symbol=str(trade.get("symbol") or symbol),
                            side=Side(str(trade.get("side"))),
                            price=float(trade.get("price")),
                            size=float(trade.get("amount")),
                            fee=fee_cost,
                            timestamp=ts,
                        )
                        await self._fills.put(fill)
                        if timestamp is not None:
                            next_since = int(timestamp) + 1
                            previous = self._last_trade_since.get(symbol)
                            if previous is None or next_since > previous:
                                self._last_trade_since[symbol] = next_since
                        if len(self._seen_trade_ids) > 5000:
                            self._seen_trade_ids = {trade_id}
            except asyncio.CancelledError:  # pragma: no cover - cooperative cancellation
                raise
            except Exception as exc:
                logger.exception("error polling fills for %s: %s", self._venue, exc)
            await asyncio.sleep(self._fill_poll_interval)

    def _require_exchange(self) -> CCXTExchange:
        if self._exchange is None:
            raise RuntimeError("Exchange connector not started")
        return self._exchange

    async def _call(self, func: Callable, *args, **kwargs):
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(5),
            wait=wait_exponential_jitter(initial=0.2, max=5.0),
            retry=retry_if_exception_type((NetworkError, RateLimitExceeded)),
            reraise=True,
        ):
            with attempt:
                return await func(*args, **kwargs)

    async def fetch_balance(self) -> Dict[str, float]:
        if self._paper_exchange:
            return {}
        exchange = self._require_exchange()
        balances = await self._call(exchange.fetch_balance)
        result: Dict[str, float] = {}
        free = balances.get("free") or {}
        total = balances.get("total") or {}
        for asset, amount in free.items():
            result[str(asset)] = float(amount)
        for asset, amount in total.items():
            key = str(asset)
            result[key] = max(result.get(key, 0.0), float(amount))
        return result

    async def fetch_order_status(self, order_id: str, symbol: Optional[str] = None) -> Optional[OrderStatus]:
        if self._paper_exchange:
            orders = await self._paper_exchange.list_orders(symbol)
            for state in orders:
                if state.order.order_id == order_id:
                    return OrderStatus(
                        order_id=order_id,
                        symbol=state.order.symbol,
                        side=state.order.side,
                        price=state.order.price,
                        size=state.order.size,
                        remaining=state.remaining,
                        status=state.status,
                    )
            return None
        exchange = self._require_exchange()
        raw = await self._call(exchange.fetch_order, order_id, symbol)
        return OrderStatus(
            order_id=str(raw.get("id") or order_id),
            symbol=str(raw.get("symbol") or symbol or ""),
            side=Side(str(raw.get("side"))),
            price=float(raw.get("price")),
            size=float(raw.get("amount")),
            remaining=float(raw.get("remaining") or 0.0),
            status=str(raw.get("status", "unknown")),
        )


__all__ = ["ExchangeConnector", "PaperExchange", "OrderState"]
