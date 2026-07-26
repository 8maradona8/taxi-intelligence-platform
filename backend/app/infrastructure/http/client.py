import asyncio
from time import perf_counter
from typing import Any

import httpx

from app.core.logging import logger
from app.infrastructure.http.exceptions import (
    HttpRequestError,
    HttpResponseError,
    HttpTimeoutError,
)


class AsyncHttpClient:
    RETRYABLE_STATUS_CODES = {
        429,
        500,
        502,
        503,
        504,
    }

    def __init__(
        self,
        *,
        base_url: str = "",
        timeout_seconds: float = 10.0,
        max_retries: int = 3,
        backoff_seconds: float = 1.0,
        default_headers: dict[str, str] | None = None,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")

        if max_retries < 0:
            raise ValueError("max_retries cannot be negative")

        if backoff_seconds < 0:
            raise ValueError("backoff_seconds cannot be negative")

        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds

        headers = {
            "Accept": "application/json",
            "User-Agent": "Taxi-Intelligence-Platform/0.1.0",
        }

        if default_headers:
            headers.update(default_headers)

        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(timeout_seconds),
            headers=headers,
            follow_redirects=True,
        )

    async def get_json(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        response = await self._get(
            url,
            params=params,
            headers=headers,
        )

        try:
            return response.json()
        except ValueError as exc:
            raise HttpResponseError(
                status_code=response.status_code,
                message="Response body is not valid JSON",
                url=str(response.url),
            ) from exc

    async def get_text(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> str:
        response = await self._get(
            url,
            params=params,
            headers=headers,
        )

        return response.text

    async def _get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        attempts = self.max_retries + 1

        for attempt in range(1, attempts + 1):
            started_at = perf_counter()

            try:
                logger.info(
                    "External HTTP request started: "
                    f"method=GET url={url} attempt={attempt}/{attempts}"
                )

                response = await self._client.get(
                    url,
                    params=params,
                    headers=headers,
                )

                elapsed_ms = round(
                    (perf_counter() - started_at) * 1000,
                    2,
                )

                logger.info(
                    "External HTTP response received: "
                    f"method=GET url={response.url} "
                    f"status={response.status_code} "
                    f"duration_ms={elapsed_ms} "
                    f"attempt={attempt}/{attempts}"
                )

                if (
                    response.status_code in self.RETRYABLE_STATUS_CODES
                    and attempt < attempts
                ):
                    await self._wait_before_retry(
                        attempt=attempt,
                        reason=f"HTTP {response.status_code}",
                        url=str(response.url),
                    )
                    continue

                response.raise_for_status()
                return response

            except httpx.TimeoutException as exc:
                request_url = self._request_url(exc, fallback=url)

                if attempt < attempts:
                    await self._wait_before_retry(
                        attempt=attempt,
                        reason=exc.__class__.__name__,
                        url=request_url,
                    )
                    continue

                raise HttpTimeoutError(
                    f"Request to {request_url} timed out after {attempts} attempts"
                ) from exc

            except httpx.HTTPStatusError as exc:
                raise HttpResponseError(
                    status_code=exc.response.status_code,
                    message=self._response_message(exc.response),
                    url=str(exc.request.url),
                ) from exc

            except httpx.RequestError as exc:
                request_url = self._request_url(exc, fallback=url)

                if attempt < attempts:
                    await self._wait_before_retry(
                        attempt=attempt,
                        reason=exc.__class__.__name__,
                        url=request_url,
                    )
                    continue

                raise HttpRequestError(
                    f"Request to {request_url} failed after {attempts} attempts: {exc}"
                ) from exc

        raise HttpRequestError(f"Request to {url} failed unexpectedly")

    async def _wait_before_retry(
        self,
        *,
        attempt: int,
        reason: str,
        url: str,
    ) -> None:
        delay = self.backoff_seconds * (2 ** (attempt - 1))

        logger.warning(
            "External HTTP request will be retried: "
            f"url={url} reason={reason} "
            f"retry_in_seconds={delay} "
            f"completed_attempt={attempt}"
        )

        await asyncio.sleep(delay)

    @staticmethod
    def _request_url(
        exc: httpx.RequestError,
        *,
        fallback: str,
    ) -> str:
        request = getattr(exc, "request", None)

        if request is None:
            return fallback

        return str(request.url)

    @staticmethod
    def _response_message(response: httpx.Response) -> str:
        body = response.text.strip()

        if not body:
            return response.reason_phrase or "External service error"

        return body[:500]

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncHttpClient":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object | None,
    ) -> None:
        await self.close()
