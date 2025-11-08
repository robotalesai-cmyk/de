"""Trade and quote storage adapters."""

from __future__ import annotations

import asyncio
import importlib.util
import sqlite3
from typing import Optional

from ..core.types import OrderBookSnapshot, Trade

_aiosqlite_spec = importlib.util.find_spec("aiosqlite")
if _aiosqlite_spec is not None:
    import aiosqlite  # type: ignore
else:
    aiosqlite = None  # type: ignore


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
        async with self._lock:
            if self._use_aiosqlite and aiosqlite is not None and self._conn is not None:
                await self._conn.execute(
                    "INSERT INTO snapshots VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        snapshot.timestamp.isoformat(),
                        snapshot.venue,
                        snapshot.symbol,
                        snapshot.bid.price,
                        snapshot.ask.price,
                        snapshot.bid.size,
                        snapshot.ask.size,
                    ),
                )
                await self._conn.commit()
            else:
                assert isinstance(self._conn, sqlite3.Connection)
                await asyncio.to_thread(
                    self._conn.execute,
                    "INSERT INTO snapshots VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        snapshot.timestamp.isoformat(),
                        snapshot.venue,
                        snapshot.symbol,
                        snapshot.bid.price,
                        snapshot.ask.price,
                        snapshot.bid.size,
                        snapshot.ask.size,
                    ),
                )
                await asyncio.to_thread(self._conn.commit)

    async def record_trade(self, trade: Trade) -> None:
        async with self._lock:
            if self._use_aiosqlite and aiosqlite is not None and self._conn is not None:
                await self._conn.execute(
                    "INSERT INTO trades VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        trade.timestamp.isoformat(),
                        trade.venue,
                        trade.symbol,
                        trade.price,
                        trade.size,
                        trade.side.value,
                    ),
                )
                await self._conn.commit()
            else:
                assert isinstance(self._conn, sqlite3.Connection)
                await asyncio.to_thread(
                    self._conn.execute,
                    "INSERT INTO trades VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        trade.timestamp.isoformat(),
                        trade.venue,
                        trade.symbol,
                        trade.price,
                        trade.size,
                        trade.side.value,
                    ),
                )
                await asyncio.to_thread(self._conn.commit)

    async def close(self) -> None:
        if self._use_aiosqlite and aiosqlite is not None and self._conn is not None:
            await self._conn.close()
        elif isinstance(self._conn, sqlite3.Connection):
            await asyncio.to_thread(self._conn.close)
        self._conn = None


async def create_storage(backend: str, dsn: str) -> StorageBackend:
    if backend == "sqlite":
        storage = SQLiteStorage(dsn)
        await storage.connect()
        return storage
    raise ValueError(f"Unsupported storage backend: {backend}")
