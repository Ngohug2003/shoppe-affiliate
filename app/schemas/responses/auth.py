from app.schemas.base import ApiResponseSchema


class TokenResponse(ApiResponseSchema):
    access_token: str
    token_type: str = "bearer"


class UserResponse(ApiResponseSchema):
    id: int
    email: str
    is_active: bool
    is_admin: bool
