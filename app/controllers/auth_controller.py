from fastapi import HTTPException, status
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
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return TokenResponse(access_token=self.service.create_token(user))

    async def current_user(self, session: AsyncSession, token: str) -> User:
        user = await self.service.get_user_from_token(session, token)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    @staticmethod
    def require_admin(user: User) -> User:
        if not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrator access is required",
            )
        return user
