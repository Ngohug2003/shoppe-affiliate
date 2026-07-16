from app.repositories.health_repository import HealthRepository


class HealthService:
    def __init__(self, repository: HealthRepository) -> None:
        self.repository = repository

    async def is_postgres_ready(self) -> bool:
        return await self.repository.check_postgres()
