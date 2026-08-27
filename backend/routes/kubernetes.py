from fastapi import APIRouter, Depends

from backend.api_state import get_service
from backend.services.finops_service import FinOpsService

router = APIRouter(prefix="/api/kubernetes", tags=["kubernetes"])


@router.get("/overview")
def overview(service: FinOpsService = Depends(get_service)):
    return service.k8s_overview()


@router.get("/clusters")
def clusters(service: FinOpsService = Depends(get_service)):
    return service.k8s_clusters()


@router.get("/nodes")
def nodes(service: FinOpsService = Depends(get_service)):
    return service.k8s_nodes_response()


@router.get("/namespaces")
def namespaces(service: FinOpsService = Depends(get_service)):
    return {**service._envelope(), "namespaces": service.k8s_namespaces()}


@router.get("/workloads")
def workloads(service: FinOpsService = Depends(get_service)):
    return service.k8s_workloads_response()


@router.get("/recommendations")
def recommendations(service: FinOpsService = Depends(get_service)):
    return service.k8s_recommendations()


@router.get("/cost-history")
def cost_history(service: FinOpsService = Depends(get_service)):
    return service.k8s_history()
