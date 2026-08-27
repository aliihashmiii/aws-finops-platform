"""Cost analyzer facade; cross-platform aggregation lives in FinOpsService."""

from backend.services.finops_service import FinOpsService


def analyze_costs(service: FinOpsService) -> dict:
    return service.costs()
