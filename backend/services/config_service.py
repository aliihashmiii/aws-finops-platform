"""Configuration service for demo/live analysis and UI settings."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from threading import Lock
from typing import Any, Dict

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config.yaml"

DEFAULTS: Dict[str, Any] = {
    "analysis": {"idle_cpu_threshold": 5.0, "idle_days": 7, "old_snapshot_days": 90},
    "governance": {"required_tags": ["Environment", "Team", "CostCenter"]},
    "forecast": {"horizon_months": 6, "growth_rate": 0.05},
    "kubernetes": {
        "cpu_efficiency_threshold": 0.40,
        "memory_efficiency_threshold": 0.50,
        "node_utilization_threshold": 0.30,
        "safety_margin": 0.20,
    },
    "ai_finops": {"monthly_budget": 5000.0, "alert_threshold": 80.0, "high_cost_request": 0.10},
    "application": {"mode": "demo", "region": "us-east-1"},
}


def _merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge(merged[key], value)
        else:
            merged[key] = value
    return merged


class ConfigService:
    def __init__(self, path: Path = CONFIG_PATH) -> None:
        self.path = path
        self._lock = Lock()
        self._values = self._load()

    def _load(self) -> Dict[str, Any]:
        try:
            raw = yaml.safe_load(self.path.read_text()) or {}
        except (OSError, yaml.YAMLError) as exc:
            # The API remains usable with safe defaults, but surfaces the issue in health data.
            raw = {"_load_error": str(exc)}
        return _merge(DEFAULTS, raw)

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return deepcopy(self._values)

    def get(self, section: str, key: str, default: Any = None) -> Any:
        return self.snapshot().get(section, {}).get(key, default)

    def update(self, patch: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            for section, values in patch.items():
                if isinstance(values, dict):
                    self._values.setdefault(section, {}).update(values)
            return deepcopy(self._values)

    def save(self) -> None:
        with self._lock:
            serializable = {k: v for k, v in self._values.items() if not k.startswith("_")}
            self.path.write_text(yaml.safe_dump(serializable, sort_keys=False))

    @property
    def load_error(self) -> str | None:
        return self._values.get("_load_error")
