from app.schemas.responses.health import DependencyStatus, LiveResponse, ReadyResponse
from app.services.health_service import HealthService


class PublicHealthController:
    def __init__(self, service: HealthService) -> None:
        self.service = service

    @staticmethod
    def live() -> LiveResponse:
        return LiveResponse(status="ok")

    async def ready(self) -> ReadyResponse:
        postgres_ready = await self.service.is_postgres_ready()
        response = ReadyResponse(
            status="ready" if postgres_ready else "not_ready",
            dependencies=DependencyStatus(
                postgres="ok" if postgres_ready else "unavailable"
            ),
        )
        return response
