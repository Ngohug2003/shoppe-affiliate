from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.controllers.health_controller import HealthController
from app.db.session import engine
from app.repositories.health_repository import HealthRepository
from app.schemas.health import LiveResponse, ReadyResponse
from app.services.health_service import HealthService

router = APIRouter(prefix="/health", tags=["health"])
health_controller = HealthController(HealthService(HealthRepository(engine)))


@router.get("/live", response_model=LiveResponse)
async def live() -> LiveResponse:
    return health_controller.live()


@router.get("/ready", response_model=ReadyResponse)
async def ready() -> ReadyResponse | JSONResponse:
    return await health_controller.ready()
