from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.auth_controller import AuthController
from app.db.session import get_db_session
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/oauth2-token")
auth_controller = AuthController()


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    return await auth_controller.current_user(session, token)


async def require_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    return auth_controller.require_admin(current_user)
