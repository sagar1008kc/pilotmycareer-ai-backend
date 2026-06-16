"""Typed application errors and FastAPI exception handlers."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.logging import get_logger

logger = get_logger("app.errors")


class AppError(Exception):
    """Base class for expected, client-facing errors."""

    status_code: int = 400
    code: str = "app_error"

    def __init__(self, message: str, *, status_code: int | None = None, code: str | None = None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        if code is not None:
            self.code = code


class AuthError(AppError):
    status_code = 401
    code = "auth_error"


class ForbiddenError(AppError):
    status_code = 403
    code = "forbidden"


class ValidationAppError(AppError):
    status_code = 422
    code = "validation_error"


class UpstreamError(AppError):
    status_code = 502
    code = "upstream_error"


def _error_body(code: str, message: str, request_id: str | None) -> dict:
    body: dict[str, object] = {"error": {"code": code, "message": message}}
    if request_id:
        body["request_id"] = request_id
    return body


def register_exception_handlers(app: FastAPI) -> None:
    """Attach JSON exception handlers that preserve the request id."""

    @app.exception_handler(AppError)
    async def _handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.warning(exc.message, extra={"request_id": request_id})
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.code, exc.message, request_id),
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=422,
            content={
                "error": {"code": "validation_error", "message": "Invalid request payload"},
                "details": exc.errors(),
                "request_id": request_id,
            },
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.exception("Unhandled error", extra={"request_id": request_id})
        return JSONResponse(
            status_code=500,
            content=_error_body("internal_error", "Internal server error", request_id),
        )
