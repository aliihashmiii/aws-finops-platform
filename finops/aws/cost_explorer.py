"""Cost Explorer adapter helpers.

The live collector owns AWS calls today; these focused helpers document the next extraction point
without duplicating billing logic in the frontend.
"""

from __future__ import annotations

from typing import Any, Dict


def summarize_groups(response: Dict[str, Any]) -> Dict[str, float]:
    """Normalize a Cost Explorer grouped response into service -> amount."""
    result: Dict[str, float] = {}
    for group in response.get("ResultsByTime", [{}])[0].get("Groups", []):
        keys = group.get("Keys", [])
        metric = group.get("Metrics", {}).get("UnblendedCost", {})
        if keys and "Amount" in metric:
            result[keys[0]] = round(float(metric["Amount"]), 2)
    return result
