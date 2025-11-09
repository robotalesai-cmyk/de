from __future__ import annotations

import json
import sys
from types import SimpleNamespace

import pytest

pytest.importorskip("pydantic")

if "yaml" not in sys.modules:  # pragma: no cover - test-only fallback
    sys.modules["yaml"] = SimpleNamespace(
        safe_load=json.loads,
        safe_dump=json.dumps,
    )

from bot.core.config import StrategyConfig


def test_strategy_config_loads_relative_venues(tmp_path):
    venues_path = tmp_path / "venues.yaml"
    venues_payload = json.dumps(
        {
            "test-venue": {
                "rest_base": "https://api.test",
                "ws_public": "wss://test",
                "has_paper": True,
                "rate_limits": [],
            }
        }
    )
    venues_path.write_text(venues_payload, encoding="utf-8")

    config_path = tmp_path / "config.yaml"
    config_payload = json.dumps(
        {
            "symbols": [
                {
                    "name": "BTC-USDT",
                    "venue": "test-venue",
                    "tick_size": 0.5,
                    "lot_size": 0.001,
                    "max_order_notional": 1000,
                    "account_notional_cap": 2000,
                    "max_position": 1.0,
                    "hedge_ratio": 1.0,
                    "basis_capture": False,
                    "maker_fee_bps": -1.0,
                    "taker_fee_bps": 5.0,
                    "post_only": True,
                    "allow_taker": True,
                    "max_orders": 5,
                }
            ],
            "risk": {
                "max_drawdown": 0.05,
                "max_daily_loss": 0.02,
                "max_inventory_notional": 1000,
                "max_open_orders": 10,
                "kill_switch_threshold": 3,
            },
            "latency_budget_ms": 200,
            "quote": {
                "gamma": 0.1,
                "horizon_seconds": 10,
                "kappa": 1.5,
                "min_spread": 0.1,
                "refresh_seconds": 1.0,
                "skew_alpha": 0.0,
            },
            "inventory": {"target": 0.0, "soft_limit": 0.1, "hard_limit": 0.2},
            "hedge": {
                "enabled": True,
                "rebalance_threshold": 0.05,
                "max_notional": 1000,
                "hedge_ratio": 1.0,
                "mode": "perp",
                "cooldown_seconds": 1.0,
            },
            "basis": {
                "enabled": False,
                "max_notional": 0.0,
                "target_notional": 0.0,
                "funding_threshold": 0.0,
            },
            "venues_config": venues_path.name,
            "storage": {"backend": "sqlite", "dsn": "sqlite:///tmp.db"},
            "metrics": {"host": "127.0.0.1", "port": 9010},
        }
    )
    config_path.write_text(config_payload, encoding="utf-8")

    config = StrategyConfig.load(config_path)
    venues = config.load_venues()
    assert venues.get("test-venue").rest_base == "https://api.test"
