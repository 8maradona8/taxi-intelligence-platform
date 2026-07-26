from app.infrastructure.http import AsyncHttpClient


class SofiaAirportWebsiteClient:
    """Downloads public flight information from Sofia Airport."""

    ARRIVALS_PATH = "/en/flights/arrivals/"
    DEPARTURES_PATH = "/en/flights/departures/"

    def __init__(
        self,
        http_client: AsyncHttpClient,
    ) -> None:
        self._http_client = http_client

    async def get_arrivals_html(self) -> str:
        """Return the public Sofia Airport arrivals page as HTML."""

        return await self._http_client.get_text(
            self.ARRIVALS_PATH,
            params={
                "flights": "scroll",
            },
        )

    async def get_departures_html(self) -> str:
        """Return the public Sofia Airport departures page as HTML."""

        return await self._http_client.get_text(
            self.DEPARTURES_PATH,
            params={
                "flights": "scroll",
            },
        )
