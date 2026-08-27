"""Provider-neutral AI unit-cost calculations."""


def total_tokens(input_tokens: int, output_tokens: int) -> int:
    return int(input_tokens) + int(output_tokens)


def cost_per_request(cost: float, request_count: int) -> float:
    return round(cost / request_count, 6) if request_count else 0.0


def cost_per_1k_tokens(cost: float, input_tokens: int, output_tokens: int) -> float:
    total = total_tokens(input_tokens, output_tokens)
    return round(cost / total * 1000, 6) if total else 0.0
