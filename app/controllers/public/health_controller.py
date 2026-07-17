from fastapi import status
from fastapi.responses import JSONResponse

from app.schemas.responses.health import DependencyStatus, LiveResponse, ReadyResponse
from app.services.health_service import HealthService


class PublicHealthController:
    def __init__(self, service: HealthService) -> None:
        self.service = service

    @staticmethod
    def live() -> LiveResponse:
        return LiveResponse(status="ok")

    async def ready(self) -> ReadyResponse | JSONResponse:
        postgres_ready = await self.service.is_postgres_ready()
        response = ReadyResponse(
            status="ready" if postgres_ready else "not_ready",
            dependencies=DependencyStatus(
                postgres="ok" if postgres_ready else "unavailable"
            ),
        )
        if postgres_ready:
            return response
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=response.model_dump(),
        )
