from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.responses.auth import TokenResponse
from app.services.auth_service import AuthService


class AuthController:
    def __init__(self, service: AuthService | None = None) -> None:
        self.service = service or AuthService()

    async def login(
        self, session: AsyncSession, email: str, password: str
    ) -> TokenResponse:
        user = await self.service.authenticate(session, email, password)
        return TokenResponse(access_token=self.service.create_token(user))

    async def current_user(self, session: AsyncSession, token: str) -> User:
        return await self.service.get_user_from_token(session, token)

    def require_admin(self, user: User) -> User:
        return self.service.require_admin(user)
