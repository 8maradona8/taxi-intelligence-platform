from typing import Any

from app.infrastructure.http import AsyncHttpClient


class MetNorwayWeatherClient:
    LOCATION_FORECAST_PATH = "/weatherapi/locationforecast/2.0/compact"

    def __init__(
        self,
        *,
        http_client: AsyncHttpClient,
        user_agent: str,
    ) -> None:
        normalized_user_agent = user_agent.strip()

        if not normalized_user_agent:
            raise ValueError("user_agent cannot be empty")

        if normalized_user_agent == ("Taxi-Intelligence-Platform/0.1.0"):
            raise ValueError("user_agent must include identifiable contact information")

        self._http_client = http_client
        self._user_agent = normalized_user_agent

    async def get_location_forecast(
        self,
        *,
        latitude: float,
        longitude: float,
        altitude: int | None = None,
    ) -> dict[str, Any]:
        self._validate_coordinates(
            latitude=latitude,
            longitude=longitude,
        )

        if altitude is not None and not -500 <= altitude <= 9000:
            raise ValueError("altitude must be between -500 and 9000 metres")

        params: dict[str, Any] = {
            "lat": latitude,
            "lon": longitude,
        }

        if altitude is not None:
            params["altitude"] = altitude

        payload = await self._http_client.get_json(
            self.LOCATION_FORECAST_PATH,
            params=params,
            headers={
                "Accept": "application/json",
                "User-Agent": self._user_agent,
            },
        )

        if not isinstance(payload, dict):
            raise ValueError("MET Norway response must be a JSON object")

        return payload

    @staticmethod
    def _validate_coordinates(
        *,
        latitude: float,
        longitude: float,
    ) -> None:
        if not -90.0 <= latitude <= 90.0:
            raise ValueError("latitude must be between -90 and 90")

        if not -180.0 <= longitude <= 180.0:
            raise ValueError("longitude must be between -180 and 180")
