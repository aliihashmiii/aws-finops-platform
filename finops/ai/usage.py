"""Normalize AI provider usage records from an optional JSON telemetry file."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List


REQUIRED = {"provider", "model", "timestamp", "application", "team", "environment", "input_tokens", "output_tokens", "request_count", "latency_ms", "cost"}


def normalize_usage(record: Dict[str, Any]) -> Dict[str, Any]:
    missing = REQUIRED - set(record)
    if missing:
        raise ValueError(f"AI usage record missing fields: {', '.join(sorted(missing))}")
    item = dict(record)
    item["input_tokens"] = int(item["input_tokens"])
    item["output_tokens"] = int(item["output_tokens"])
    item["request_count"] = int(item["request_count"])
    item["latency_ms"] = float(item["latency_ms"])
    item["cost"] = float(item["cost"])
    item["cache_hit_rate"] = float(item.get("cache_hit_rate", 0))
    item["total_tokens"] = item["input_tokens"] + item["output_tokens"]
    return item


def load_usage_from_file() -> List[Dict[str, Any]]:
    path_value = os.getenv("FINOPS_AI_USAGE_FILE")
    if not path_value:
        return []
    path = Path(path_value)
    try:
        raw = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Unable to load FINOPS_AI_USAGE_FILE: {exc}") from exc
    records = raw.get("usage", raw) if isinstance(raw, dict) else raw
    if not isinstance(records, list):
        raise ValueError("AI usage JSON must be a list or an object with a usage list")
    return [normalize_usage(record) for record in records]
