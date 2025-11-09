"""Configuration loading utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, PrivateAttr, validator


class SymbolConfig(BaseModel):
    """Configuration for a single trading symbol."""

    name: str
    venue: str
    tick_size: float = Field(..., gt=0)
    lot_size: float = Field(..., gt=0)
    max_order_notional: float = Field(..., gt=0)
    max_position: float = Field(..., ge=0)
    hedge_ratio: float = Field(1.0, ge=0)
    basis_capture: bool = False
    max_cancels_per_minute: Optional[int] = None


class RiskConfig(BaseModel):
    max_drawdown: float = Field(..., gt=0)
    max_daily_loss: float = Field(..., gt=0)
    max_inventory_notional: float = Field(..., gt=0)
    kill_switch_threshold: int = Field(3, ge=1)


class QuoteConfig(BaseModel):
    model: str = "avellaneda_stoikov"
    gamma: float = Field(..., gt=0)
    horizon_seconds: float = Field(..., gt=0)
    kappa: float = Field(..., gt=0)
    min_spread: float = Field(0.0, ge=0)
    refresh_seconds: float = Field(1.0, gt=0)
    skew_alpha: float = Field(0.0)


class InventoryConfig(BaseModel):
    target: float = 0.0
    soft_limit: float = Field(..., ge=0)
    hard_limit: float = Field(..., ge=0)

    @validator("hard_limit")
    def _check_limits(cls, v: float, values: Dict[str, Any]) -> float:
        soft = values.get("soft_limit", 0.0)
        if v < soft:
            raise ValueError("hard_limit must be >= soft_limit")
        return v


class HedgeConfig(BaseModel):
    enabled: bool = True
    rebalance_threshold: float = Field(0.05, ge=0)
    max_notional: float = Field(..., gt=0)
    mode: str = Field("perp")


class BasisConfig(BaseModel):
    enabled: bool = False
    max_notional: float = Field(0.0, ge=0)
    funding_threshold: float = Field(0.0, ge=0)


class StorageConfig(BaseModel):
    backend: str = Field("sqlite")
    dsn: str


class MetricsConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = Field(9001, ge=1)


class StrategyConfig(BaseModel):
    """Aggregated strategy configuration."""

    symbols: List[SymbolConfig]
    risk: RiskConfig
    latency_budget_ms: int = Field(500, ge=0)
    quote: QuoteConfig
    inventory: InventoryConfig
    hedge: HedgeConfig
    basis: BasisConfig
    venues_config: str
    storage: StorageConfig
    metrics: MetricsConfig
    _base_path: Path = PrivateAttr(default=Path.cwd())

    @classmethod
    def load(cls, path: str | Path) -> "StrategyConfig":
        cfg_path = Path(path)
        with cfg_path.open("r", encoding="utf-8") as handle:
            data: Dict[str, Any] = yaml.safe_load(handle)
        config = cls.model_validate(data)
        config._base_path = cfg_path.parent.resolve()
        return config

    def load_venues(self) -> Dict[str, Any]:
        venues_path = Path(self.venues_config)
        if not venues_path.is_absolute():
            venues_path = (self._base_path / venues_path).resolve()
        with venues_path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle)


class VenueRateLimit(BaseModel):
    type: str
    limit: int
    interval: int


class VenueConfig(BaseModel):
    rest_base: str
    ws_public: str
    ws_private: Optional[str] = None
    rate_limits: List[VenueRateLimit] = Field(default_factory=list)
    has_paper: bool = False
    funding_endpoint: Optional[str] = None


class Venues(BaseModel):
    __root__: Dict[str, VenueConfig]

    def get(self, venue: str) -> VenueConfig:
        try:
            return self.__root__[venue]
        except KeyError as exc:
            raise KeyError(f"Unknown venue: {venue}") from exc


def load_venues_config(path: str | Path) -> Venues:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return Venues.model_validate({"__root__": data})
