"""Process-local service registry for the lightweight portfolio deployment."""

from backend.services.finops_service import FinOpsService

service = FinOpsService()


def get_service() -> FinOpsService:
    return service
