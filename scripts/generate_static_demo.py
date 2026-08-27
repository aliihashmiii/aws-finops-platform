#!/usr/bin/env python3
"""Export the deterministic control-plane demo contract for static hosting."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.services.finops_service import FinOpsService

OUTS = [ROOT / "frontend" / "demo-api", ROOT / "docs" / "demo-api"]


def main() -> None:
    for output in OUTS:
        output.mkdir(parents=True, exist_ok=True)
    service = FinOpsService(mode="demo")
    payloads = {
        "health": service.health(),
        "mode": {"mode": service.mode, "account_id": service.data.get("account_id"), "region": service.data.get("region"), "warnings": service.warnings},
        "dashboard": service.dashboard(),
        "costs": service.costs(),
        "cost-history": service.cost_history(),
        "waste": service.waste(),
        "recommendations": service.recommendations(),
        "recommendations-aws": {**service._envelope(), "total_potential_savings": sum(x["estimated_monthly_savings"] for x in service._aws_findings()), "recommendations": service._aws_findings()},
        "forecast": service.forecast(),
        "governance": service.governance(),
        "settings": service.settings(),
        "kubernetes-overview": service.k8s_overview(),
        "kubernetes-clusters": service.k8s_clusters(),
        "kubernetes-nodes": service.k8s_nodes_response(),
        "kubernetes-namespaces": {**service._envelope(), "namespaces": service.k8s_namespaces()},
        "kubernetes-workloads": service.k8s_workloads_response(),
        "kubernetes-recommendations": service.k8s_recommendations(),
        "kubernetes-cost-history": service.k8s_history(),
        "ai-overview": service.ai_overview(),
        "ai-usage": service.ai_usage_response(),
        "ai-cost-history": service.ai_history(),
        "ai-models": {**service._envelope(), "models": service.ai_models()},
        "ai-applications": {**service._envelope(), "applications": service.ai_applications()},
        "ai-recommendations": service.ai_recommendations(),
        "ai-anomalies": service.ai_anomalies(),
        "ai-unit-economics": service.ai_unit_economics(),
    }
    for output in OUTS:
        for name, payload in payloads.items():
            (output / f"{name}.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {len(payloads)} fixtures to {len(OUTS)} static targets")


if __name__ == "__main__":
    main()
