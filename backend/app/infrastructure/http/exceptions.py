class HttpClientError(Exception):
    """Base exception for external HTTP client failures."""


class HttpTimeoutError(HttpClientError):
    """Raised when an external HTTP request times out."""


class HttpRequestError(HttpClientError):
    """Raised when an external HTTP request cannot be completed."""


class HttpResponseError(HttpClientError):
    """Raised when an external service returns an unsuccessful response."""

    def __init__(
        self,
        *,
        status_code: int,
        message: str,
        url: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.message = message
        self.url = url

        location = f" for {url}" if url else ""

        super().__init__(
            f"External service returned HTTP {status_code}{location}: {message}"
        )