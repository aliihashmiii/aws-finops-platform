"""Safe Kubernetes request recommendations and a node bin-packing estimate."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List


def recommended_request(observed_usage: float, safety_margin: float, minimum: float = 0.1) -> float:
    """Return an observed-usage estimate plus margin; callers must validate SLOs."""
    return round(max(minimum, observed_usage * (1 + safety_margin)), 2)


def _fits(nodes: List[Dict[str, Any]], pods: List[Dict[str, Any]], headroom: float) -> bool:
    """First-fit-decreasing check that every pod fits into ``nodes`` leaving ``headroom``."""
    free = {n["node_id"]: [n["cpu_capacity"] * (1 - headroom) - n.get("reserved_cpu", 0), n["memory_capacity"] * (1 - headroom) - n.get("reserved_memory", 0)] for n in nodes}
    order = sorted(pods, key=lambda p: (p["cpu"] / max(1e-9, max(n["cpu_capacity"] for n in nodes))) + (p["memory"] / max(1e-9, max(n["memory_capacity"] for n in nodes))), reverse=True)
    for pod in order:
        target = next((nid for nid, (cpu, mem) in free.items() if cpu >= pod["cpu"] and mem >= pod["memory"]), None)
        if target is None:
            return False
        free[target][0] -= pod["cpu"]
        free[target][1] -= pod["memory"]
    return True


def removable_nodes(nodes: Iterable[Dict[str, Any]], pods: Iterable[Dict[str, Any]], headroom: float = 0.25) -> List[str]:
    """Greedily drain the least-utilized nodes while all (rightsized) pods still fit.

    ``pods`` carry ``cpu`` and ``memory`` (the request each pod would have after
    rightsizing). Per-node DaemonSet overhead should be passed as ``reserved_cpu`` and
    ``reserved_memory`` on each node, because it disappears with the node.
    This is an estimate: it ignores affinity, topology spread and PDBs.
    """
    remaining = list(nodes)
    pods = list(pods)
    removed: List[str] = []
    if not pods or not remaining:
        return removed
    for candidate in sorted(remaining, key=lambda n: (n.get("utilization", 0), -n.get("monthly_cost", 0))):
        trial = [n for n in remaining if n["node_id"] != candidate["node_id"]]
        if trial and _fits(trial, pods, headroom):
            remaining = trial
            removed.append(candidate["node_id"])
    return removed
