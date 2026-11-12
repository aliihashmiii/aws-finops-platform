"""Explainable anomaly calculations for AI spend and token telemetry."""

from __future__ import annotations

from typing import Dict


def percent_change(current: float, baseline: float) -> float:
    if baseline == 0:
        return 0.0 if current == 0 else 100.0
    return round((current - baseline) / baseline * 100, 2)


def is_spike(current: float, baseline: float, threshold: float = 25.0) -> bool:
    return percent_change(current, baseline) >= threshold


def decompose_change(previous: Dict[str, float], current: Dict[str, float]) -> Dict[str, float]:
    """Split a spend change into volume, intensity and price drivers.

    cost = requests x tokens_per_request x cost_per_token, so the percentage change of
    each factor explains where the movement came from (a log-style decomposition).
    """
    def ratio(key_num: str, key_den: str | None, src: Dict[str, float]) -> float:
        num = float(src.get(key_num, 0))
        if key_den is None:
            return num
        den = float(src.get(key_den, 0))
        return num / den if den else 0.0

    prev_tokens = previous.get("input_tokens", 0) + previous.get("output_tokens", 0)
    curr_tokens = current.get("input_tokens", 0) + current.get("output_tokens", 0)
    prev_tpr = prev_tokens / previous["request_count"] if previous.get("request_count") else 0
    curr_tpr = curr_tokens / current["request_count"] if current.get("request_count") else 0
    prev_cpt = previous.get("cost", 0) / prev_tokens if prev_tokens else 0
    curr_cpt = current.get("cost", 0) / curr_tokens if curr_tokens else 0
    return {
        "spend_change_pct": percent_change(current.get("cost", 0), previous.get("cost", 0)),
        "request_change_pct": percent_change(ratio("request_count", None, current), ratio("request_count", None, previous)),
        "tokens_per_request_change_pct": percent_change(curr_tpr, prev_tpr),
        "input_tokens_change_pct": percent_change(current.get("input_tokens", 0), previous.get("input_tokens", 0)),
        "unit_price_change_pct": percent_change(curr_cpt, prev_cpt),
    }


def primary_driver(drivers: Dict[str, float]) -> str:
    labels = {
        "request_change_pct": "request volume growth",
        "tokens_per_request_change_pct": "larger prompts or responses per request",
        "unit_price_change_pct": "model mix or unit price change",
    }
    key = max(labels, key=lambda k: abs(drivers.get(k, 0)))
    return labels[key]
