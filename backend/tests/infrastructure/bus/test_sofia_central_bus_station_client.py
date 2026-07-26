import pytest

from app.infrastructure.clients import (
    SofiaCentralBusStationClient,
)


class FakeHttpClient:
    def __init__(self) -> None:
        self.received_url: str | None = None
        self.received_params: dict[str, object] | None = None
        self.received_headers: dict[str, str] | None = None

    async def get_text(
        self,
        url: str,
        *,
        params: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
    ) -> str:
        self.received_url = url
        self.received_params = params
        self.received_headers = headers

        return "<html>bus-arrivals</html>"


@pytest.mark.anyio
async def test_client_downloads_bus_arrivals_html() -> None:
    http_client = FakeHttpClient()

    client = SofiaCentralBusStationClient(
        http_client=http_client,  # type: ignore[arg-type]
    )

    html = await client.get_arrivals_html(
        hours=2,
    )

    assert http_client.received_url == "/"
    assert http_client.received_params == {
        "mod": "06a943c59f33a34bb5924aaf72cd2995",
        "t": 2,
        "d": "c",
    }
    assert http_client.received_headers is None
    assert html == "<html>bus-arrivals</html>"


@pytest.mark.anyio
@pytest.mark.parametrize(
    "hours",
    [
        1,
        2,
        4,
        8,
        12,
    ],
)
async def test_client_accepts_supported_horizons(
    hours: int,
) -> None:
    http_client = FakeHttpClient()

    client = SofiaCentralBusStationClient(
        http_client=http_client,  # type: ignore[arg-type]
    )

    await client.get_arrivals_html(
        hours=hours,
    )

    assert http_client.received_params is not None
    assert http_client.received_params["t"] == hours


@pytest.mark.anyio
@pytest.mark.parametrize(
    "hours",
    [
        0,
        3,
        6,
        24,
    ],
)
async def test_client_rejects_unsupported_horizon(
    hours: int,
) -> None:
    http_client = FakeHttpClient()

    client = SofiaCentralBusStationClient(
        http_client=http_client,  # type: ignore[arg-type]
    )

    with pytest.raises(
        ValueError,
        match="hours must be one of",
    ):
        await client.get_arrivals_html(
            hours=hours,
        )

    assert http_client.received_url is None
