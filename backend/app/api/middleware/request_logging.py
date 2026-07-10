from time import perf_counter
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.logging import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next,
    ) -> Response:
        request_id = request.headers.get(
            "X-Request-ID",
            str(uuid4()),
        )

        request.state.request_id = request_id

        started_at = perf_counter()

        logger.info(
            "API request started: "
            f"request_id={request_id} "
            f"method={request.method} "
            f"path={request.url.path}"
        )

        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = round(
                (perf_counter() - started_at) * 1000,
                2,
            )

            logger.exception(
                "API request failed: "
                f"request_id={request_id} "
                f"method={request.method} "
                f"path={request.url.path} "
                f"duration_ms={elapsed_ms}"
            )

            raise

        elapsed_ms = round(
            (perf_counter() - started_at) * 1000,
            2,
        )

        response.headers["X-Request-ID"] = request_id

        logger.info(
            "API request completed: "
            f"request_id={request_id} "
            f"method={request.method} "
            f"path={request.url.path} "
            f"status={response.status_code} "
            f"duration_ms={elapsed_ms}"
        )

        return response
