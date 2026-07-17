from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.tags import AUTH_TAG
from app.controllers.auth_controller import AuthController
from app.db.session import get_db_session
from app.middlewares.auth import get_current_user
from app.models.user import User
from app.schemas.base import ApiResponse, success_response
from app.schemas.responses.auth import TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=[AUTH_TAG])
auth_controller = AuthController()


async def _authenticate(
    form: OAuth2PasswordRequestForm,
    session: AsyncSession,
) -> TokenResponse:
    return await auth_controller.login(session, form.username, form.password)


@router.post("/token", response_model=ApiResponse[TokenResponse])
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[TokenResponse]:
    token = await _authenticate(form, session)
    return success_response(token, message="Đăng nhập thành công")


@router.post(
    "/oauth2-token",
    response_model=TokenResponse,
    include_in_schema=False,
)
async def oauth2_login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> TokenResponse:
    return await _authenticate(form, session)


@router.get("/me", response_model=ApiResponse[UserResponse])
async def me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[UserResponse]:
    return success_response(
        UserResponse.model_validate(current_user),
        message="Lấy thông tin người dùng thành công",
    )
