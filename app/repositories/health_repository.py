from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine


class HealthRepository:
    def __init__(self, engine: AsyncEngine) -> None:
        self.engine = engine

    async def check_postgres(self) -> bool:
        try:
            async with self.engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
            return True
        except (OSError, SQLAlchemyError):
            return False
