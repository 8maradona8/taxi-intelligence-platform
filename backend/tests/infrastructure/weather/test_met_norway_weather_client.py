from typing import Any

import pytest

from app.infrastructure.clients import (
    MetNorwayWeatherClient,
)


class FakeHttpClient:
    def __init__(self) -> None:
        self.received_url: str | None = None
        self.received_params: dict[str, Any] | None = None
        self.received_headers: dict[str, str] | None = None
        self.response: Any = {
            "type": "Feature",
            "properties": {
                "timeseries": [],
            },
        }

    async def get_json(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        self.received_url = url
        self.received_params = params
        self.received_headers = headers

        return self.response


@pytest.mark.anyio
async def test_client_downloads_location_forecast() -> None:
    http_client = FakeHttpClient()

    client = MetNorwayWeatherClient(
        http_client=http_client,  # type: ignore[arg-type]
        user_agent=("Taxi-Intelligence-Platform/0.1 contact@example.com"),
    )

    payload = await client.get_location_forecast(
        latitude=42.6977,
        longitude=23.3219,
        altitude=550,
    )

    assert http_client.received_url == ("/weatherapi/locationforecast/2.0/compact")
    assert http_client.received_params == {
        "lat": 42.6977,
        "lon": 23.3219,
        "altitude": 550,
    }
    assert http_client.received_headers == {
        "Accept": "application/json",
        "User-Agent": ("Taxi-Intelligence-Platform/0.1 contact@example.com"),
    }
    assert payload["type"] == "Feature"


@pytest.mark.anyio
async def test_client_omits_optional_altitude() -> None:
    http_client = FakeHttpClient()

    client = MetNorwayWeatherClient(
        http_client=http_client,  # type: ignore[arg-type]
        user_agent=("Taxi-Intelligence-Platform/0.1 contact@example.com"),
    )

    await client.get_location_forecast(
        latitude=42.6977,
        longitude=23.3219,
    )

    assert http_client.received_params == {
        "lat": 42.6977,
        "lon": 23.3219,
    }


@pytest.mark.parametrize(
    ("latitude", "longitude"),
    [
        (-90.1, 23.3219),
        (90.1, 23.3219),
        (42.6977, -180.1),
        (42.6977, 180.1),
    ],
)
@pytest.mark.anyio
async def test_client_rejects_invalid_coordinates(
    latitude: float,
    longitude: float,
) -> None:
    http_client = FakeHttpClient()

    client = MetNorwayWeatherClient(
        http_client=http_client,  # type: ignore[arg-type]
        user_agent=("Taxi-Intelligence-Platform/0.1 contact@example.com"),
    )

    with pytest.raises(ValueError):
        await client.get_location_forecast(
            latitude=latitude,
            longitude=longitude,
        )

    assert http_client.received_url is None


@pytest.mark.parametrize(
    "altitude",
    [
        -501,
        9001,
    ],
)
@pytest.mark.anyio
async def test_client_rejects_invalid_altitude(
    altitude: int,
) -> None:
    http_client = FakeHttpClient()

    client = MetNorwayWeatherClient(
        http_client=http_client,  # type: ignore[arg-type]
        user_agent=("Taxi-Intelligence-Platform/0.1 contact@example.com"),
    )

    with pytest.raises(
        ValueError,
        match="altitude must be between",
    ):
        await client.get_location_forecast(
            latitude=42.6977,
            longitude=23.3219,
            altitude=altitude,
        )


@pytest.mark.parametrize(
    "user_agent",
    [
        "",
        "   ",
        "Taxi-Intelligence-Platform/0.1.0",
    ],
)
def test_client_rejects_unidentifiable_user_agent(
    user_agent: str,
) -> None:
    with pytest.raises(ValueError):
        MetNorwayWeatherClient(
            http_client=FakeHttpClient(),  # type: ignore[arg-type]
            user_agent=user_agent,
        )


@pytest.mark.anyio
async def test_client_rejects_non_object_response() -> None:
    http_client = FakeHttpClient()
    http_client.response = []

    client = MetNorwayWeatherClient(
        http_client=http_client,  # type: ignore[arg-type]
        user_agent=("Taxi-Intelligence-Platform/0.1 contact@example.com"),
    )

    with pytest.raises(
        ValueError,
        match="response must be a JSON object",
    ):
        await client.get_location_forecast(
            latitude=42.6977,
            longitude=23.3219,
        )
