"""Finding identity, savings basis, and overlap-aware savings aggregation.

Two controls keep the savings number honest:

1. Identity: one finding per ``platform + resource_id + category`` (``dedupe_findings``).
2. Overlap: different findings can target the same dollars (e.g. routing a workload to a
   cheaper model *and* caching it). Findings that share an ``overlap_group`` with a
   ``baseline_cost`` are combined multiplicatively, so two 50% reductions on $100 yield
   $75, not $100. Only ``savings_basis == "cash"`` findings count toward totals;
   ``"allocation"`` findings (e.g. Kubernetes request reductions) move showback cost
   between owners and become cash only when nodes are removed.
"""

from __future__ import annotations

from collections import OrderedDict, defaultdict
from typing import Any, Dict, Iterable, List, Optional


def finding_id(platform: str, resource_id: str, category: str) -> str:
    return f"{platform.lower()}:{resource_id}:{category}".replace(" ", "-").lower()


def make_finding(
    *, platform: str, resource_id: str, resource_type: str, service: str, category: str,
    issue: str, recommendation: str, savings: float, confidence: str, priority: str,
    risk: str, source: str, explanation: str, calculation: str = "",
    savings_basis: Optional[str] = None, overlap_group: Optional[str] = None,
    baseline_cost: Optional[float] = None,
) -> Dict[str, Any]:
    amount = round(max(0.0, savings), 2)
    basis = savings_basis or ("cash" if amount > 0 else "none")
    return {
        "id": finding_id(platform, resource_id, category),
        "platform": platform,
        "resource_id": resource_id,
        "resource_type": resource_type,
        "service": service,
        "category": category,
        "issue": issue,
        "recommendation": recommendation,
        "estimated_monthly_savings": amount,
        "savings_basis": basis,
        "overlap_group": overlap_group,
        "baseline_cost": round(baseline_cost, 2) if baseline_cost is not None else None,
        "confidence": confidence,
        "priority": priority,
        "risk": risk,
        "source": source,
        "explanation": explanation,
        "calculation": calculation,
    }


def dedupe_findings(findings: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Keep one opportunity per stable identity, retaining the strongest estimate."""
    unique: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
    for finding in findings:
        current = unique.get(finding["id"])
        if current is None or finding["estimated_monthly_savings"] > current["estimated_monthly_savings"]:
            unique[finding["id"]] = finding
    return list(unique.values())


def total_savings(findings: Iterable[Dict[str, Any]]) -> float:
    """Sum unique, cash-basis savings with overlap groups combined multiplicatively."""
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    total = 0.0
    for item in dedupe_findings(findings):
        if item.get("savings_basis", "cash") != "cash" or item["estimated_monthly_savings"] <= 0:
            continue
        group = item.get("overlap_group")
        if group and item.get("baseline_cost"):
            groups[group].append(item)
        else:
            total += item["estimated_monthly_savings"]
    for items in groups.values():
        baseline = max(i["baseline_cost"] for i in items)
        remaining = 1.0
        for i in items:
            remaining *= 1 - min(1.0, i["estimated_monthly_savings"] / baseline)
        total += baseline * (1 - remaining)
    return round(total, 2)


def gross_savings(findings: Iterable[Dict[str, Any]]) -> float:
    """Naive sum of cash findings, shown next to ``total_savings`` to make overlap visible."""
    return round(sum(i["estimated_monthly_savings"] for i in dedupe_findings(findings) if i.get("savings_basis", "cash") == "cash"), 2)
