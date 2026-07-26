from datetime import datetime

from app.domain import BusArrival
from app.infrastructure.clients import (
    SofiaCentralBusStationClient,
)
from app.infrastructure.mappers import (
    SofiaCentralBusArrivalParser,
)


class SofiaCentralBusStationCollector:
    def __init__(
        self,
        *,
        client: SofiaCentralBusStationClient,
        parser: SofiaCentralBusArrivalParser,
        horizon_hours: int = 2,
    ) -> None:
        if horizon_hours not in client.ALLOWED_HORIZON_HOURS:
            allowed_values = ", ".join(
                str(value) for value in sorted(client.ALLOWED_HORIZON_HOURS)
            )

            raise ValueError(f"horizon_hours must be one of: {allowed_values}")

        self._client = client
        self._parser = parser
        self._horizon_hours = horizon_hours

    async def collect_arrivals(
        self,
        *,
        observed_at: datetime | None = None,
    ) -> list[BusArrival]:
        html = await self._client.get_arrivals_html(
            hours=self._horizon_hours,
        )

        return self._parser.parse_arrivals(
            html,
            observed_at=observed_at,
        )
