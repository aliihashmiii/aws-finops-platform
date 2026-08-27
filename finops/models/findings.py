"""Finding identity and savings aggregation shared by all analysis modules."""

from __future__ import annotations

from collections import OrderedDict
from typing import Any, Dict, Iterable, List


def finding_id(platform: str, resource_id: str, category: str) -> str:
    return f"{platform.lower()}:{resource_id}:{category}".replace(" ", "-").lower()


def make_finding(
    *, platform: str, resource_id: str, resource_type: str, service: str, category: str,
    issue: str, recommendation: str, savings: float, confidence: str, priority: str,
    risk: str, source: str, explanation: str,
) -> Dict[str, Any]:
    return {
        "id": finding_id(platform, resource_id, category),
        "platform": platform,
        "resource_id": resource_id,
        "resource_type": resource_type,
        "service": service,
        "category": category,
        "issue": issue,
        "recommendation": recommendation,
        "estimated_monthly_savings": round(max(0.0, savings), 2),
        "confidence": confidence,
        "priority": priority,
        "risk": risk,
        "source": source,
        "explanation": explanation,
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
    return round(sum(item["estimated_monthly_savings"] for item in dedupe_findings(findings)), 2)
