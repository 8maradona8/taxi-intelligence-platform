import asyncio

from app.infrastructure.clients import SofiaAirportWebsiteClient
from app.infrastructure.http import AsyncHttpClient
from app.infrastructure.mappers import SofiaAirportFlightParser


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
        client = SofiaAirportWebsiteClient(
            http_client=http_client,
        )

        html = await client.get_arrivals_html()

    flights = SofiaAirportFlightParser().parse_arrivals(html)

    print("Parsed flights:", len(flights))

    for flight in flights[:10]:
        print("---")
        print("Flight:", flight.flight_number)
        print(
            "Origin:",
            flight.origin_city,
            flight.origin_iata,
        )
        print("Scheduled:", flight.scheduled_arrival)
        print("Effective:", flight.effective_arrival)
        print("Status:", flight.status)
        print("Terminal:", flight.terminal)
        print("Airline:", flight.airline)
        print("Delay minutes:", flight.delay_minutes)


if __name__ == "__main__":
    asyncio.run(main())
