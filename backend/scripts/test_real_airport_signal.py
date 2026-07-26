import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from app.infrastructure.clients import SofiaAirportWebsiteClient
from app.infrastructure.collectors import SofiaAirportCollector
from app.infrastructure.http import AsyncHttpClient
from app.infrastructure.mappers import (
    AirportSignalMapper,
    SofiaAirportFlightParser,
)


SOFIA_TIMEZONE = ZoneInfo("Europe/Sofia")


async def main() -> None:
    async with AsyncHttpClient(
        base_url="https://sofia-airport.eu",
        timeout_seconds=20.0,
        max_retries=2,
        backoff_seconds=1.0,
        default_headers={
            "Accept": "text/html,application/xhtml+xml",
            "User-Agent": (
                "Taxi-Intelligence-Platform/0.1.0 "
                "(development; public flight data reader)"
            ),
        },
    ) as http_client:
        collector = SofiaAirportCollector(
            client=SofiaAirportWebsiteClient(
                http_client=http_client,
            ),
            parser=SofiaAirportFlightParser(),
        )

        flights = await collector.collect_arrivals()

    observed_at = datetime.now(SOFIA_TIMEZONE)

    signal = AirportSignalMapper().map_arrivals(
        flights,
        observed_at=observed_at,
    )

    print("Airport signal created")
    print("Observed at:", signal.observed_at)
    print("Zone:", signal.zone_name)
    print("Impact:", signal.impact_score.value)
    print("Confidence:", signal.confidence.value)
    print("Priority:", signal.priority)
    print("Payload:", signal.payload)


if __name__ == "__main__":
    asyncio.run(main())
