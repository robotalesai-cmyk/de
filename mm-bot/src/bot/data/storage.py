"""Trade and quote storage adapters."""

"""Persistence backends for recording snapshots and trades."""

from __future__ import annotations

import asyncio
import importlib.util
import sqlite3
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

from ..core.types import OrderBookSnapshot, Trade

_aiosqlite_spec = importlib.util.find_spec("aiosqlite")
if _aiosqlite_spec is not None:  # pragma: no cover - optional dependency
    import aiosqlite  # type: ignore
else:  # pragma: no cover - fallback when aiosqlite missing
    aiosqlite = None  # type: ignore

_clickhouse_spec = importlib.util.find_spec("clickhouse_connect")
if _clickhouse_spec is not None:  # pragma: no cover - optional dependency
    import clickhouse_connect  # type: ignore
else:  # pragma: no cover - fallback when clickhouse unavailable
    clickhouse_connect = None  # type: ignore


class StorageBackend:
    async def connect(self) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    async def record_snapshot(self, snapshot: OrderBookSnapshot) -> None:  # pragma: no cover
        raise NotImplementedError

    async def record_trade(self, trade: Trade) -> None:  # pragma: no cover
        raise NotImplementedError

    async def close(self) -> None:  # pragma: no cover
        raise NotImplementedError


class SQLiteStorage(StorageBackend):
    def __init__(self, dsn: str) -> None:
        if not dsn.startswith("sqlite:///"):
            raise ValueError("dsn must be sqlite:/// path")
        self._path = dsn.replace("sqlite:///", "")
        self._conn: Optional[object] = None
        self._lock = asyncio.Lock()
        self._use_aiosqlite = aiosqlite is not None

    async def connect(self) -> None:
        if self._use_aiosqlite and aiosqlite is not None:
            self._conn = await aiosqlite.connect(self._path)
            await self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS snapshots (
                    ts TEXT,
                    venue TEXT,
                    symbol TEXT,
                    bid REAL,
                    ask REAL,
                    bid_size REAL,
                    ask_size REAL
                )
                """
            )
            await self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trades (
                    ts TEXT,
                    venue TEXT,
                    symbol TEXT,
                    price REAL,
                    size REAL,
                    side TEXT
                )
                """
            )
            await self._conn.commit()
        else:
            conn = sqlite3.connect(self._path)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS snapshots (
                    ts TEXT,
                    venue TEXT,
                    symbol TEXT,
                    bid REAL,
                    ask REAL,
                    bid_size REAL,
                    ask_size REAL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trades (
                    ts TEXT,
                    venue TEXT,
                    symbol TEXT,
                    price REAL,
                    size REAL,
                    side TEXT
                )
                """
            )
            conn.commit()
            conn.close()
            self._conn = sqlite3.connect(self._path, check_same_thread=False)

    async def record_snapshot(self, snapshot: OrderBookSnapshot) -> None:
        payload = (
            snapshot.timestamp.isoformat(),
            snapshot.venue,
            snapshot.symbol,
            snapshot.bid.price,
            snapshot.ask.price,
            snapshot.bid.size,
            snapshot.ask.size,
        )
        async with self._lock:
            if self._use_aiosqlite and aiosqlite is not None and self._conn is not None:
                await self._conn.execute(
                    "INSERT INTO snapshots VALUES (?, ?, ?, ?, ?, ?, ?)",
                    payload,
                )
                await self._conn.commit()
            else:
                assert isinstance(self._conn, sqlite3.Connection)
                await asyncio.to_thread(
                    self._conn.execute,
                    "INSERT INTO snapshots VALUES (?, ?, ?, ?, ?, ?, ?)",
                    payload,
                )
                await asyncio.to_thread(self._conn.commit)

    async def record_trade(self, trade: Trade) -> None:
        payload = (
            trade.timestamp.isoformat(),
            trade.venue,
            trade.symbol,
            trade.price,
            trade.size,
            trade.side.value,
        )
        async with self._lock:
            if self._use_aiosqlite and aiosqlite is not None and self._conn is not None:
                await self._conn.execute(
                    "INSERT INTO trades VALUES (?, ?, ?, ?, ?, ?)",
                    payload,
                )
                await self._conn.commit()
            else:
                assert isinstance(self._conn, sqlite3.Connection)
                await asyncio.to_thread(
                    self._conn.execute,
                    "INSERT INTO trades VALUES (?, ?, ?, ?, ?, ?)",
                    payload,
                )
                await asyncio.to_thread(self._conn.commit)

    async def close(self) -> None:
        if self._use_aiosqlite and aiosqlite is not None and self._conn is not None:
            await self._conn.close()
        elif isinstance(self._conn, sqlite3.Connection):
            await asyncio.to_thread(self._conn.close)
        self._conn = None


@dataclass
class ClickHouseParams:
    host: str
    port: int
    username: str
    password: str
    database: str
    secure: bool = False


class ClickHouseStorage(StorageBackend):
    def __init__(self, dsn: str) -> None:
        if clickhouse_connect is None:
            raise RuntimeError("clickhouse-connect is required for ClickHouse storage")
        self._params = self._parse_dsn(dsn)
        self._client: Optional[object] = None
        self._lock = asyncio.Lock()

    def _parse_dsn(self, dsn: str) -> ClickHouseParams:
        url = urlparse(dsn)
        if url.scheme != "clickhouse":
            raise ValueError("ClickHouse DSN must start with clickhouse://")
        host = url.hostname or "localhost"
        port = url.port or 9000
        username = url.username or "default"
        password = url.password or ""
        database = url.path.lstrip("/") or "default"
        secure = url.query.lower().find("secure=true") >= 0
        return ClickHouseParams(
            host=host,
            port=port,
            username=username,
            password=password,
            database=database,
            secure=secure,
        )

    async def connect(self) -> None:
        assert clickhouse_connect is not None
        self._client = await asyncio.to_thread(
            clickhouse_connect.get_client,
            host=self._params.host,
            port=self._params.port,
            username=self._params.username,
            password=self._params.password,
            database=self._params.database,
            secure=self._params.secure,
        )
        await asyncio.to_thread(
            self._client.command,
            """
            CREATE TABLE IF NOT EXISTS snapshots (
                ts DateTime64(3),
                venue String,
                symbol String,
                bid Float64,
                ask Float64,
                bid_size Float64,
                ask_size Float64
            ) ENGINE = MergeTree()
            ORDER BY (symbol, ts)
            """,
        )
        await asyncio.to_thread(
            self._client.command,
            """
            CREATE TABLE IF NOT EXISTS trades (
                ts DateTime64(3),
                venue String,
                symbol String,
                price Float64,
                size Float64,
                side String
            ) ENGINE = MergeTree()
            ORDER BY (symbol, ts)
            """,
        )

    async def record_snapshot(self, snapshot: OrderBookSnapshot) -> None:
        if self._client is None:
            return
        payload = [
            (
                snapshot.timestamp,
                snapshot.venue,
                snapshot.symbol,
                snapshot.bid.price,
                snapshot.ask.price,
                snapshot.bid.size,
                snapshot.ask.size,
            )
        ]
        async with self._lock:
            await asyncio.to_thread(
                self._client.insert,
                "snapshots",
                payload,
                column_names=["ts", "venue", "symbol", "bid", "ask", "bid_size", "ask_size"],
            )

    async def record_trade(self, trade: Trade) -> None:
        if self._client is None:
            return
        payload = [
            (
                trade.timestamp,
                trade.venue,
                trade.symbol,
                trade.price,
                trade.size,
                trade.side.value,
            )
        ]
        async with self._lock:
            await asyncio.to_thread(
                self._client.insert,
                "trades",
                payload,
                column_names=["ts", "venue", "symbol", "price", "size", "side"],
            )

    async def close(self) -> None:
        if self._client is None:
            return
        await asyncio.to_thread(self._client.close)
        self._client = None


async def create_storage(backend: str, dsn: str) -> StorageBackend:
    if backend == "sqlite":
        storage = SQLiteStorage(dsn)
        await storage.connect()
        return storage
    if backend == "clickhouse":
        storage = ClickHouseStorage(dsn)
        await storage.connect()
        return storage
    raise ValueError(f"Unsupported storage backend: {backend}")
