"""Pure predicates for Kubernetes waste classification."""


def over_requested(actual: float, requested: float, threshold: float) -> bool:
    return requested <= 0 or actual / requested < threshold


def underutilized_node(cpu_usage: float, cpu_capacity: float, memory_usage: float, memory_capacity: float, threshold: float) -> bool:
    cpu = cpu_usage / cpu_capacity if cpu_capacity else 0
    memory = memory_usage / memory_capacity if memory_capacity else 0
    return (cpu + memory) / 2 < threshold
