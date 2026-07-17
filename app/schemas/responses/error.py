from app.schemas.base import ApiResponse, ApiResponseSchema


class ErrorDetail(ApiResponseSchema):
    field: str
    message: str
    type: str


class ErrorData(ApiResponseSchema):
    details: list[ErrorDetail]


class ErrorResponse(ApiResponse[ErrorData]):
    pass
