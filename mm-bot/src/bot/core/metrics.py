"""Metrics collection and exposition."""

from __future__ import annotations

import asyncio
import importlib.util
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

FastAPIType: Optional[type] = None
PlainTextResponseType: Optional[type] = None
uvicorn_mod = None

if importlib.util.find_spec("fastapi") is not None:
    from fastapi import FastAPI as FastAPIType  # type: ignore[assignment]
    from fastapi.responses import PlainTextResponse as PlainTextResponseType  # type: ignore[assignment]
if importlib.util.find_spec("uvicorn") is not None:
    import uvicorn as uvicorn_mod  # type: ignore[assignment]


@dataclass
class SymbolMetrics:
    inventory: float = 0.0
    pnl: float = 0.0
    spread: float = 0.0


@dataclass
class MetricsCollector:
    funding_accrual: float = 0.0
    hedge_notional: float = 0.0
    error_rate: float = 0.0
    _symbols: Dict[str, SymbolMetrics] = field(default_factory=dict)

    def record(self, symbol: str, inventory: float, pnl: float, spread: float) -> None:
        metrics = self._symbols.setdefault(symbol, SymbolMetrics())
        metrics.inventory = inventory
        metrics.pnl = pnl
        metrics.spread = spread

    def prometheus(self) -> str:
        lines = [
            "# HELP pnl_realized Realized PnL",
            "# TYPE pnl_realized gauge",
        ]
        for symbol, metrics in self._symbols.items():
            lines.append(f'pnl_realized{{symbol="{symbol}"}} {metrics.pnl}')
            lines.append(f'inventory{{symbol="{symbol}"}} {metrics.inventory}')
            lines.append(f'spread_target{{symbol="{symbol}"}} {metrics.spread}')
        lines.append(f'funding_accrual {self.funding_accrual}')
        lines.append(f'hedge_notional {self.hedge_notional}')
        lines.append(f'error_rate {self.error_rate}')
        return "\n".join(lines) + "\n"


class MetricsService:
    def __init__(self, collector: MetricsCollector, host: str, port: int) -> None:
        self._collector = collector
        self._host = host
        self._port = port
        self._server: Optional[Any] = None
        self._task: Optional[asyncio.Task[None]] = None
        self._app = self._create_app()

    def _create_app(self):
        if FastAPIType is None:
            raise RuntimeError("FastAPI is required for metrics service")
        app = FastAPIType()

        @app.get("/health")
        async def health() -> Dict[str, str]:
            return {"status": "ok"}

        @app.get("/metrics")
        async def metrics() -> PlainTextResponseType:  # type: ignore[valid-type]
            assert PlainTextResponseType is not None
            return PlainTextResponseType(self._collector.prometheus())

        return app

    async def start(self) -> None:
        if uvicorn_mod is None:
            raise RuntimeError("uvicorn is required to expose metrics")
        config = uvicorn_mod.Config(self._app, host=self._host, port=self._port, log_level="info", loop="asyncio")
        self._server = uvicorn_mod.Server(config)
        self._task = asyncio.create_task(self._server.serve())

    async def stop(self) -> None:
        if self._server is not None:
            self._server.should_exit = True
        if self._task is not None:
            await self._task
