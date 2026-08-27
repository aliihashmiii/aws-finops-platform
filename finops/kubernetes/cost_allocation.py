"""Transparent Kubernetes allocation math used by the control-plane model."""


def efficiency(actual: float, requested: float) -> float:
    return round(actual / requested, 4) if requested > 0 else 0.0


def split_cost(monthly_cost: float, cpu_share: float = 0.55) -> dict[str, float]:
    cpu = round(monthly_cost * cpu_share, 2)
    return {"cpu_cost": cpu, "memory_cost": round(monthly_cost - cpu, 2)}


def unallocated_cost(cluster_cost: float, allocated_cost: float) -> float:
    return round(max(0.0, cluster_cost - allocated_cost), 2)
