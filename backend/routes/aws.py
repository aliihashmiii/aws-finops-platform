from fastapi import APIRouter, Depends, Query

from backend.api_state import get_service
from finops.models.findings import finding_id
from backend.services.finops_service import FinOpsService

router = APIRouter(prefix="/api", tags=["aws"])


@router.get("/costs")
def costs(service: FinOpsService = Depends(get_service)):
    return service.costs()


@router.get("/cost-history")
def cost_history(service: FinOpsService = Depends(get_service)):
    return service.cost_history()


@router.get("/waste")
def waste(service: FinOpsService = Depends(get_service)):
    return service.waste()


@router.get("/recommendations")
def recommendations(platform: str | None = Query(default=None), service: FinOpsService = Depends(get_service)):
    items = service.recommendations()
    if platform:
        items["recommendations"] = [item for item in items["recommendations"] if item["platform"].lower() == platform.lower()]
    return items


@router.get("/forecast")
def forecast(service: FinOpsService = Depends(get_service)):
    return service.forecast()


@router.get("/governance")
def governance(service: FinOpsService = Depends(get_service)):
    return service.governance()


@router.get("/recommendations/{recommendation_id}")
def explain_recommendation(recommendation_id: str, service: FinOpsService = Depends(get_service)):
    return service.explain(recommendation_id)
