from datetime import date

from app.domain import TrainArrival
from app.infrastructure.clients import BdzLiveBoardClient
from app.infrastructure.mappers import SofiaRailwayArrivalParser


class SofiaRailwayCollector:
    def __init__(
        self,
        *,
        client: BdzLiveBoardClient,
        parser: SofiaRailwayArrivalParser,
    ) -> None:
        self._client = client
        self._parser = parser

    async def collect_arrivals(
        self,
        *,
        service_date: date,
    ) -> list[TrainArrival]:
        html = await self._client.get_sofia_arrivals_html()

        return self._parser.parse_arrivals(
            html,
            service_date=service_date,
        )
