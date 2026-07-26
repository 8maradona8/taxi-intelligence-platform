from app.domain import WeatherForecast
from app.infrastructure.clients import (
    MetNorwayWeatherClient,
)
from app.infrastructure.mappers import (
    MetNorwayForecastParser,
)


class SofiaWeatherCollector:
    SOFIA_LATITUDE = 42.6977
    SOFIA_LONGITUDE = 23.3219
    SOFIA_ALTITUDE_METRES = 550

    def __init__(
        self,
        *,
        client: MetNorwayWeatherClient,
        parser: MetNorwayForecastParser,
        latitude: float = SOFIA_LATITUDE,
        longitude: float = SOFIA_LONGITUDE,
        altitude: int | None = SOFIA_ALTITUDE_METRES,
    ) -> None:
        if not -90.0 <= latitude <= 90.0:
            raise ValueError("latitude must be between -90 and 90")

        if not -180.0 <= longitude <= 180.0:
            raise ValueError("longitude must be between -180 and 180")

        if altitude is not None and not -500 <= altitude <= 9000:
            raise ValueError("altitude must be between -500 and 9000 metres")

        self._client = client
        self._parser = parser
        self._latitude = latitude
        self._longitude = longitude
        self._altitude = altitude

    async def collect_forecasts(
        self,
    ) -> list[WeatherForecast]:
        payload = await self._client.get_location_forecast(
            latitude=self._latitude,
            longitude=self._longitude,
            altitude=self._altitude,
        )

        return self._parser.parse_forecasts(payload)
