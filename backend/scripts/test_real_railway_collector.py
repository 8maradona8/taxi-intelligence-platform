import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from app.infrastructure.clients import BdzLiveBoardClient
from app.infrastructure.collectors import SofiaRailwayCollector
from app.infrastructure.http import AsyncHttpClient
from app.infrastructure.mappers import (
    SofiaRailwayArrivalParser,
)


SOFIA_TIMEZONE = ZoneInfo("Europe/Sofia")


async def main() -> None:
    service_date = datetime.now(SOFIA_TIMEZONE).date()

    async with AsyncHttpClient(
        base_url="https://live.bdz.bg",
        timeout_seconds=20.0,
        max_retries=2,
        backoff_seconds=1.0,
        default_headers={
            "Accept": "text/html,application/xhtml+xml",
            "User-Agent": (
                "Taxi-Intelligence-Platform/0.1.0 (public railway data reader)"
            ),
        },
    ) as http_client:
        collector = SofiaRailwayCollector(
            client=BdzLiveBoardClient(
                http_client=http_client,
            ),
            parser=SofiaRailwayArrivalParser(),
        )

        arrivals = await collector.collect_arrivals(
            service_date=service_date,
        )

    print("Service date:", service_date)
    print("Railway arrivals:", len(arrivals))

    for arrival in arrivals:
        print("---")
        print("Train:", arrival.train_number)
        print(
            "Type:",
            arrival.train_type_code,
            arrival.train_type_name,
        )
        print("Origin:", arrival.origin_station)
        print(
            "Scheduled:",
            arrival.scheduled_arrival,
        )
        print(
            "Expected:",
            arrival.expected_arrival,
        )
        print(
            "Effective:",
            arrival.effective_arrival,
        )
        print(
            "Delay minutes:",
            arrival.delay_minutes,
        )
        print("Status:", arrival.status.value)
        print("Platform:", arrival.platform)


if __name__ == "__main__":
    asyncio.run(main())
