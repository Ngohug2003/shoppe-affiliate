from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.tags import AUTH_TAG
from app.controllers.auth_controller import AuthController
from app.db.session import get_db_session
from app.middlewares.auth import get_current_user
from app.models.user import User
from app.schemas.responses.auth import TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=[AUTH_TAG])
auth_controller = AuthController()


@router.post("/token", response_model=TokenResponse)
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> TokenResponse:
    return await auth_controller.login(session, form.username, form.password)


@router.get("/me", response_model=UserResponse)
async def me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user
