"""Transparent Kubernetes cost allocation (OpenCost-style).

Each node's cost is split into a CPU pool and a memory pool using relative resource
weights. Pods are charged ``max(request, usage)`` of each resource at the node's unit
price. Whatever is left on the node is idle capacity: it stays visible, it is never
silently spread into workload cost, and it is not itself counted as savings.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, List

# Default relative weights (USD per vCPU-hour and per GiB-hour) used only to split a
# node's price between CPU and memory. Only the ratio matters.
CPU_WEIGHT = 0.031611
MEMORY_WEIGHT = 0.004237


def efficiency(actual: float, requested: float) -> float:
    return round(actual / requested, 4) if requested > 0 else 0.0


def split_cost(monthly_cost: float, cpu_share: float = 0.55) -> dict[str, float]:
    cpu = round(monthly_cost * cpu_share, 2)
    return {"cpu_cost": cpu, "memory_cost": round(monthly_cost - cpu, 2)}


def unallocated_cost(cluster_cost: float, allocated_cost: float) -> float:
    return round(max(0.0, cluster_cost - allocated_cost), 2)


def node_unit_prices(node: Dict[str, Any]) -> Dict[str, float]:
    cpu_pool = node["cpu_capacity"] * CPU_WEIGHT
    mem_pool = node["memory_capacity"] * MEMORY_WEIGHT
    total = cpu_pool + mem_pool
    if not total:
        return {"cpu": 0.0, "memory": 0.0, "cpu_share": 0.0}
    cpu_share = cpu_pool / total
    cost = float(node.get("monthly_cost", 0))
    return {
        "cpu": cost * cpu_share / node["cpu_capacity"] if node["cpu_capacity"] else 0.0,
        "memory": cost * (1 - cpu_share) / node["memory_capacity"] if node["memory_capacity"] else 0.0,
        "cpu_share": cpu_share,
    }


def allocate(nodes: Iterable[Dict[str, Any]], pods: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """Allocate node cost to pods. Returns per-pod cost and per-node idle cost."""
    nodes = list(nodes)
    by_node: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for pod in pods:
        by_node[pod["node_id"]].append(pod)
    pod_costs: List[Dict[str, Any]] = []
    node_summary: Dict[str, Dict[str, float]] = {}
    for node in nodes:
        prices = node_unit_prices(node)
        rows = []
        for pod in by_node.get(node["node_id"], []):
            cpu_units = max(pod.get("cpu_request", 0), pod.get("cpu_usage", 0))
            mem_units = max(pod.get("memory_request", 0), pod.get("memory_usage", 0))
            rows.append({**pod, "cpu_cost": cpu_units * prices["cpu"], "memory_cost": mem_units * prices["memory"]})
        allocated = sum(r["cpu_cost"] + r["memory_cost"] for r in rows)
        cost = float(node.get("monthly_cost", 0))
        if allocated > cost and allocated:
            # Usage above requests can oversubscribe a node; scale so a node is never billed twice.
            scale = cost / allocated
            for r in rows:
                r["cpu_cost"] *= scale
                r["memory_cost"] *= scale
            allocated = cost
        for r in rows:
            r["cost"] = r["cpu_cost"] + r["memory_cost"]
        pod_costs.extend(rows)
        node_summary[node["node_id"]] = {"allocated_cost": allocated, "idle_cost": max(0.0, cost - allocated), "cpu_unit_price": prices["cpu"], "memory_unit_price": prices["memory"]}
    return {"pods": pod_costs, "nodes": node_summary}
