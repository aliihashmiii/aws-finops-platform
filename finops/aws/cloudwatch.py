"""CloudWatch metric normalization helpers."""

from __future__ import annotations

from typing import Any, Dict


def average_metric(response: Dict[str, Any], metric_name: str) -> Dict[str, Any]:
    points = response.get("Datapoints", [])
    if not points:
        return {"status": "partial", "metric": metric_name, "value": None, "message": "No datapoints returned for the requested period."}
    values = [float(point["Average"]) for point in points if "Average" in point]
    if not values:
        return {"status": "partial", "metric": metric_name, "value": None, "message": "Datapoints did not include Average values."}
    return {"status": "ok", "metric": metric_name, "value": round(sum(values) / len(values), 2), "sample_count": len(values)}
