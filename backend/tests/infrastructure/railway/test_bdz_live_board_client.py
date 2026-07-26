import pytest

from app.infrastructure.clients import BdzLiveBoardClient


class FakeHttpClient:
    def __init__(self) -> None:
        self.received_url: str | None = None

    async def get_text(
        self,
        url: str,
        *,
        params: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
    ) -> str:
        self.received_url = url

        assert params is None
        assert headers is None

        return "<html>bdz-arrivals</html>"


@pytest.mark.anyio
async def test_client_downloads_sofia_arrivals_html() -> None:
    http_client = FakeHttpClient()

    client = BdzLiveBoardClient(
        http_client=http_client,  # type: ignore[arg-type]
    )

    html = await client.get_sofia_arrivals_html()

    assert http_client.received_url == "/bg/sofia/arrivals"
    assert html == "<html>bdz-arrivals</html>"
