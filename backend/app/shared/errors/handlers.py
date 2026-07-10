from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import logger
from app.infrastructure.http import (
    HttpRequestError,
    HttpResponseError,
    HttpTimeoutError,
)
from app.shared.errors.codes import ErrorCode
from app.shared.errors.models import ApiError


def _get_request_id(request: Request) -> str:
    request_id = getattr(
        request.state,
        "request_id",
        None,
    )

    return request_id or str(uuid4())


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HttpTimeoutError)
    async def handle_http_timeout(
        request: Request,
        exc: HttpTimeoutError,
    ) -> JSONResponse:
        request_id = _get_request_id(request)

        logger.warning(
            "External service timeout: "
            f"request_id={request_id} "
            f"path={request.url.path} "
            f"error={exc}"
        )

        error = ApiError.create(
            code=ErrorCode.HTTP_TIMEOUT,
            message="External service did not respond in time.",
            details=str(exc),
            request_id=request_id,
        )

        return JSONResponse(
            status_code=504,
            content=error.to_dict(),
        )

    @app.exception_handler(HttpResponseError)
    async def handle_http_response_error(
        request: Request,
        exc: HttpResponseError,
    ) -> JSONResponse:
        request_id = _get_request_id(request)

        logger.warning(
            "External service response error: "
            f"request_id={request_id} "
            f"path={request.url.path} "
            f"status={exc.status_code} "
            f"error={exc}"
        )

        error = ApiError.create(
            code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            message="External service returned an error.",
            details={
                "upstream_status": exc.status_code,
                "upstream_message": exc.message,
                "upstream_url": exc.url,
            },
            request_id=request_id,
        )

        return JSONResponse(
            status_code=502,
            content=error.to_dict(),
        )

    @app.exception_handler(HttpRequestError)
    async def handle_http_request_error(
        request: Request,
        exc: HttpRequestError,
    ) -> JSONResponse:
        request_id = _get_request_id(request)

        logger.warning(
            "External service request failed: "
            f"request_id={request_id} "
            f"path={request.url.path} "
            f"error={exc}"
        )

        error = ApiError.create(
            code=ErrorCode.HTTP_REQUEST_FAILED,
            message="External service request failed.",
            details=str(exc),
            request_id=request_id,
        )

        return JSONResponse(
            status_code=502,
            content=error.to_dict(),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation_error(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        request_id = _get_request_id(request)

        validation_details = [
            {
                "location": ".".join(str(part) for part in validation_error["loc"]),
                "message": validation_error["msg"],
                "type": validation_error["type"],
            }
            for validation_error in exc.errors()
        ]

        logger.warning(
            "Request validation failed: "
            f"request_id={request_id} "
            f"path={request.url.path} "
            f"errors={validation_details}"
        )

        error = ApiError.create(
            code=ErrorCode.VALIDATION_ERROR,
            message="Request validation failed.",
            details=validation_details,
            request_id=request_id,
        )

        return JSONResponse(
            status_code=422,
            content=error.to_dict(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        request_id = _get_request_id(request)

        if exc.status_code == 404:
            error_code = ErrorCode.NOT_FOUND
        elif exc.status_code == 422:
            error_code = ErrorCode.VALIDATION_ERROR
        else:
            error_code = ErrorCode.INTERNAL_SERVER_ERROR

        error = ApiError.create(
            code=error_code,
            message=str(exc.detail),
            request_id=request_id,
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=error.to_dict(),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        request_id = _get_request_id(request)

        logger.exception(
            "Unhandled application error: "
            f"request_id={request_id} "
            f"path={request.url.path}"
        )

        error = ApiError.create(
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            message="An unexpected internal error occurred.",
            request_id=request_id,
        )

        return JSONResponse(
            status_code=500,
            content=error.to_dict(),
        )
