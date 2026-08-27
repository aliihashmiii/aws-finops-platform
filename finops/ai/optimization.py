"""Provider-neutral AI optimization predicates."""


def excessive_context(input_tokens: int, threshold: int = 10000) -> bool:
    return input_tokens > threshold


def cache_opportunity(cache_hit_rate: float, threshold: float = 0.15) -> bool:
    return cache_hit_rate < threshold


def model_routing_candidate(cost_per_request: float, threshold: float = 0.10) -> bool:
    return cost_per_request >= threshold
