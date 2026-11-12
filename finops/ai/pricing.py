"""Provider-neutral AI unit-cost calculations and an editable model price catalog.

Catalog prices are illustrative public list prices per 1M tokens. They are used to
cost demo usage and to model "what would this traffic cost on another model". Live
telemetry should carry the provider-billed ``cost``; the catalog is then used only
for counterfactual (what-if) savings.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

PRICE_SOURCE = "Illustrative provider list prices per 1M tokens; edit MODEL_CATALOG to match your contract"

# tier: premium models are candidates for routing simple tasks to their listed alternative.
MODEL_CATALOG: Dict[str, Dict[str, Any]] = {
    "gpt-4o": {"provider": "OpenAI", "input": 2.50, "cached_input": 1.25, "output": 10.00, "tier": "premium", "alternative": "gpt-4o-mini"},
    "gpt-4o-mini": {"provider": "OpenAI", "input": 0.15, "cached_input": 0.075, "output": 0.60, "tier": "efficient", "alternative": None},
    "claude-3-5-sonnet": {"provider": "Anthropic", "input": 3.00, "cached_input": 0.30, "output": 15.00, "tier": "premium", "alternative": "claude-3-5-haiku"},
    "claude-3-5-haiku": {"provider": "Anthropic", "input": 0.80, "cached_input": 0.08, "output": 4.00, "tier": "efficient", "alternative": None},
    "gemini-1.5-pro": {"provider": "Google", "input": 1.25, "cached_input": 0.3125, "output": 5.00, "tier": "premium", "alternative": "gemini-1.5-flash"},
    "gemini-1.5-flash": {"provider": "Google", "input": 0.075, "cached_input": 0.01875, "output": 0.30, "tier": "efficient", "alternative": None},
    "amazon.nova-pro": {"provider": "AWS Bedrock", "input": 0.80, "cached_input": 0.20, "output": 3.20, "tier": "premium", "alternative": "amazon.nova-lite"},
    "amazon.nova-lite": {"provider": "AWS Bedrock", "input": 0.06, "cached_input": 0.015, "output": 0.24, "tier": "efficient", "alternative": None},
}


def total_tokens(input_tokens: int, output_tokens: int) -> int:
    return int(input_tokens) + int(output_tokens)


def cost_per_request(cost: float, request_count: int) -> float:
    return round(cost / request_count, 6) if request_count else 0.0


def cost_per_1k_tokens(cost: float, input_tokens: int, output_tokens: int) -> float:
    total = total_tokens(input_tokens, output_tokens)
    return round(cost / total * 1000, 6) if total else 0.0


def price(model: str) -> Optional[Dict[str, Any]]:
    return MODEL_CATALOG.get(model)


def token_cost(model: str, input_tokens: float, output_tokens: float, cache_hit_rate: float = 0.0) -> Optional[float]:
    """Cost of a token mix on ``model``. Cached input is billed at the cached rate."""
    p = price(model)
    if p is None:
        return None
    cached = input_tokens * cache_hit_rate
    uncached = input_tokens - cached
    return round((uncached * p["input"] + cached * p["cached_input"] + output_tokens * p["output"]) / 1_000_000, 2)


def input_cost(model: str, input_tokens: float, cache_hit_rate: float = 0.0) -> Optional[float]:
    p = price(model)
    if p is None:
        return None
    cached = input_tokens * cache_hit_rate
    return round(((input_tokens - cached) * p["input"] + cached * p["cached_input"]) / 1_000_000, 2)
