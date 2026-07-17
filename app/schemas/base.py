from pydantic import BaseModel, ConfigDict


class ApiResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ResponseStatus(ApiResponseSchema):
    code: int
    message: str = ""


class ApiResponse[DataT](ApiResponseSchema):
    status: ResponseStatus
    data: DataT | None = None


def success_response[DataT](
    data: DataT,
    *,
    code: int = 200,
    message: str = "",
) -> ApiResponse[DataT]:
    return ApiResponse(
        status=ResponseStatus(code=code, message=message),
        data=data,
    )
