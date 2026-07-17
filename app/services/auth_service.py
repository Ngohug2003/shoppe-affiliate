from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AdministratorRequiredError,
    InvalidAuthenticationError,
    InvalidCredentialsError,
)
from app.core.security import create_access_token, decode_access_token, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository


def normalize_email(email: str) -> str:
    return email.strip().lower()


class AuthService:
    def __init__(self, repository: UserRepository | None = None) -> None:
        self.repository = repository or UserRepository()

    async def authenticate(
        self, session: AsyncSession, email: str, password: str
    ) -> User:
        user = await self.repository.get_by_email(session, normalize_email(email))
        if (
            user is None
            or not user.is_active
            or not verify_password(password, user.password_hash)
        ):
            raise InvalidCredentialsError
        return user

    async def get_user_from_token(
        self, session: AsyncSession, token: str
    ) -> User:
        try:
            user_id = decode_access_token(token)
        except ValueError as exc:
            raise InvalidAuthenticationError from exc
        user = await self.repository.get_by_id(session, user_id)
        if user is None or not user.is_active:
            raise InvalidAuthenticationError
        return user

    @staticmethod
    def require_admin(user: User) -> User:
        if not user.is_admin:
            raise AdministratorRequiredError
        return user

    @staticmethod
    def create_token(user: User) -> str:
        return create_access_token(user.id)
