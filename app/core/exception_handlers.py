from http import HTTPStatus

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.core.exceptions import ApplicationError
from app.schemas.base import ResponseStatus
from app.schemas.responses.error import ErrorDetail, ErrorResponse

logger = structlog.get_logger(__name__)

def _error_response(
    *,
    status_code: int,
    message: str,
    details: list[ErrorDetail] | None = None,
) -> JSONResponse:
    payload = ErrorResponse(
        status=ResponseStatus(code=status_code, message=message),
        data=None if details is None else {"details": details},
    )
    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(mode="json"),
    )


def register_exception_handlers(application: FastAPI) -> None:
    @application.exception_handler(ApplicationError)
    async def application_error_handler(
        _: Request, exc: ApplicationError
    ) -> JSONResponse:
        return _error_response(
            status_code=exc.status_code,
            message=exc.message,
        )

    @application.exception_handler(HTTPException)
    async def http_error_handler(_: Request, exc: HTTPException) -> JSONResponse:
        try:
            default_message = HTTPStatus(exc.status_code).phrase
        except ValueError:
            default_message = "Request failed"
        message = exc.detail if isinstance(exc.detail, str) else default_message
        return _error_response(
            status_code=exc.status_code,
            message=message,
        )

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = [
            ErrorDetail(
                field=".".join(str(part) for part in error["loc"]),
                message=str(error["msg"]),
                type=str(error["type"]),
            )
            for error in exc.errors()
        ]
        return _error_response(
            status_code=422,
            message="Dữ liệu gửi lên không hợp lệ",
            details=details,
        )

    @application.exception_handler(Exception)
    async def unexpected_error_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "unhandled_api_exception",
            error_type=type(exc).__name__,
        )
        return _error_response(
            status_code=500,
            message="Hệ thống gặp lỗi, vui lòng thử lại sau",
        )
