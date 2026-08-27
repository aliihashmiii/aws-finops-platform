"""Simple, explainable anomaly calculations for AI spend and token telemetry."""


def percent_change(current: float, baseline: float) -> float:
    if baseline == 0:
        return 0.0 if current == 0 else 100.0
    return round((current - baseline) / baseline * 100, 2)


def is_spike(current: float, baseline: float, threshold: float = 25.0) -> bool:
    return percent_change(current, baseline) >= threshold
