"""Trend-based spend forecasting with explicit, explainable scenarios.

The baseline fits a constant monthly growth rate to history (least squares on log
spend). The ``optimized`` scenario subtracts identified cash savings ramped in over
``ramp_months`` at an ``adoption`` rate. The ``upper`` scenario widens the baseline by
the historical residual volatility, which is what a budget owner should plan for.
"""

from __future__ import annotations

import math
from typing import Dict, List, Sequence


def fit_growth(values: Sequence[float]) -> Dict[str, float]:
    points = [(i, math.log(v)) for i, v in enumerate(values) if v and v > 0]
    if len(points) < 3:
        return {"monthly_growth": 0.0, "volatility": 0.0, "points": len(points)}
    n = len(points)
    mean_x = sum(x for x, _ in points) / n
    mean_y = sum(y for _, y in points) / n
    sxx = sum((x - mean_x) ** 2 for x, _ in points)
    slope = sum((x - mean_x) * (y - mean_y) for x, y in points) / sxx if sxx else 0.0
    intercept = mean_y - slope * mean_x
    residuals = [y - (intercept + slope * x) for x, y in points]
    volatility = math.sqrt(sum(r * r for r in residuals) / max(1, n - 2))
    return {"monthly_growth": math.exp(slope) - 1, "volatility": volatility, "points": n}


def project(current: float, history: Sequence[float], horizon: int, savings: float, adoption: float = 0.6, ramp_months: int = 3, fallback_growth: float = 0.03) -> Dict[str, object]:
    fit = fit_growth(history)
    growth = fit["monthly_growth"] if fit["points"] >= 3 else fallback_growth
    method = "log-linear trend" if fit["points"] >= 3 else "fixed growth fallback"
    rows: List[Dict[str, float]] = []
    for month in range(1, horizon + 1):
        baseline = current * (1 + growth) ** month
        realized = savings * adoption * min(1.0, month / max(1, ramp_months))
        upper = baseline * (1 + 1.28 * fit["volatility"] * math.sqrt(month))
        rows.append({"month": month, "baseline": round(baseline, 2), "optimized": round(max(0.0, baseline - realized), 2), "upper": round(upper, 2), "realized_savings": round(realized, 2)})
    return {"method": method, "monthly_growth": round(growth, 5), "volatility": round(fit["volatility"], 5), "history_points": fit["points"], "projections": rows}
