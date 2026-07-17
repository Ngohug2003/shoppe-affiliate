from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.constants.tags import PUBLIC_HEALTH_TAG
from app.controllers.public.health_controller import PublicHealthController
from app.db.session import engine
from app.repositories.health_repository import HealthRepository
from app.schemas.base import ApiResponse, success_response
from app.schemas.responses.health import LiveResponse, ReadyResponse
from app.services.health_service import HealthService

router = APIRouter(prefix="/health", tags=[PUBLIC_HEALTH_TAG])
health_controller = PublicHealthController(HealthService(HealthRepository(engine)))


@router.get("/live", response_model=ApiResponse[LiveResponse])
async def live() -> ApiResponse[LiveResponse]:
    return success_response(health_controller.live())


@router.get("/ready", response_model=ApiResponse[ReadyResponse])
async def ready() -> ApiResponse[ReadyResponse] | JSONResponse:
    readiness = await health_controller.ready()
    if readiness.status == "ready":
        return success_response(readiness)
    payload = success_response(
        readiness,
        code=status.HTTP_503_SERVICE_UNAVAILABLE,
        message="PostgreSQL chưa sẵn sàng",
    )
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=payload.model_dump(mode="json"),
    )
