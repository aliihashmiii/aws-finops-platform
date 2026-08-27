from fastapi import APIRouter, Depends

from backend.api_state import get_service
from backend.schemas.models import SettingsPatch
from backend.services.finops_service import FinOpsService

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/health")
def health(service: FinOpsService = Depends(get_service)):
    return service.health()


@router.get("/mode")
def mode(service: FinOpsService = Depends(get_service)):
    return {"mode": service.mode, "account_id": service.data.get("account_id"), "region": service.data.get("region"), "warnings": service.warnings}


@router.get("/dashboard")
def dashboard(service: FinOpsService = Depends(get_service)):
    return service.dashboard()


@router.get("/settings")
def settings(service: FinOpsService = Depends(get_service)):
    return service.settings()


@router.patch("/settings")
def update_settings(patch: SettingsPatch, service: FinOpsService = Depends(get_service)):
    return service.update_settings(patch.model_dump(exclude_unset=True))


@router.post("/analyze")
def analyze(service: FinOpsService = Depends(get_service)):
    return service.dashboard()
