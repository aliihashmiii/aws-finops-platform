"""Safe Kubernetes request recommendations."""


def recommended_request(observed_usage: float, safety_margin: float, minimum: float = 0.1) -> float:
    """Return an observed-usage estimate plus margin; callers must validate SLOs."""
    return round(max(minimum, observed_usage * (1 + safety_margin)), 2)
