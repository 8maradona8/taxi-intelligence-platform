from app.domain.flight import Flight
from app.infrastructure.clients import SofiaAirportWebsiteClient
from app.infrastructure.mappers import SofiaAirportFlightParser


class SofiaAirportCollector:
    def __init__(
        self,
        *,
        client: SofiaAirportWebsiteClient,
        parser: SofiaAirportFlightParser,
    ) -> None:
        self._client = client
        self._parser = parser

    async def collect_arrivals(self) -> list[Flight]:
        html = await self._client.get_arrivals_html()

        return self._parser.parse_arrivals(html)
