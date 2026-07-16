from fastapi import status
from fastapi.responses import JSONResponse

from app.schemas.health import DependencyStatus, LiveResponse, ReadyResponse
from app.services.health_service import HealthService


class HealthController:
    def __init__(self, service: HealthService) -> None:
        self.service = service

    @staticmethod
    def live() -> LiveResponse:
        return LiveResponse(status="ok")

    async def ready(self) -> ReadyResponse | JSONResponse:
        postgres_ok = await self.service.is_postgres_ready()
        payload = ReadyResponse(
            status="ready" if postgres_ok else "not_ready",
            dependencies=DependencyStatus(
                postgres="ok" if postgres_ok else "unavailable"
            ),
        )
        if payload.status == "not_ready":
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=payload.model_dump(),
            )
        return payload
