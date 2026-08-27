from fastapi import APIRouter, Depends

from backend.api_state import get_service
from backend.services.finops_service import FinOpsService

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.get("/overview")
def overview(service: FinOpsService = Depends(get_service)):
    return service.ai_overview()


@router.get("/usage")
def usage(service: FinOpsService = Depends(get_service)):
    return service.ai_usage_response()


@router.get("/cost-history")
def cost_history(service: FinOpsService = Depends(get_service)):
    return service.ai_history()


@router.get("/models")
def models(service: FinOpsService = Depends(get_service)):
    return {**service._envelope(), "models": service.ai_models()}


@router.get("/applications")
def applications(service: FinOpsService = Depends(get_service)):
    return {**service._envelope(), "applications": service.ai_applications()}


@router.get("/recommendations")
def recommendations(service: FinOpsService = Depends(get_service)):
    return service.ai_recommendations()


@router.get("/anomalies")
def anomalies(service: FinOpsService = Depends(get_service)):
    return service.ai_anomalies()


@router.get("/unit-economics")
def unit_economics(service: FinOpsService = Depends(get_service)):
    return service.ai_unit_economics()
