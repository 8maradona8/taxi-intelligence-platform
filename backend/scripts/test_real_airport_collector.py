import asyncio
import json
from collections import Counter

from bs4 import BeautifulSoup

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

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    raw_statuses: Counter[str] = Counter()

    for row in soup.select("tr[data-flight]"):
        raw_flight = row.get("data-flight")

        if not isinstance(raw_flight, str):
            continue

        try:
            flight_data = json.loads(raw_flight)
        except json.JSONDecodeError:
            continue

        if flight_data.get("ad") != "A":
            continue

        raw_status = str(flight_data.get("st_en") or "").strip()

        raw_statuses[raw_status or "<empty>"] += 1

    print("Raw Sofia Airport statuses:")

    for status, count in raw_statuses.items():
        print(f"- {status}: {count}")

    parser = SofiaAirportFlightParser()
    flights = parser.parse_arrivals(html)

    print()
    print("Collected arrivals:", len(flights))

    landed = [flight for flight in flights if flight.status.value == "landed"]

    upcoming = [
        flight
        for flight in flights
        if flight.status.value
        in {
            "scheduled",
            "expected",
            "delayed",
        }
    ]

    cancelled = [flight for flight in flights if flight.is_cancelled]

    print("Landed:", len(landed))
    print("Upcoming:", len(upcoming))
    print("Cancelled:", len(cancelled))

    status_counts = Counter(flight.status.value for flight in flights)

    print("Mapped statuses:")

    for status, count in status_counts.items():
        print(f"- {status}: {count}")

    for flight in flights[:5]:
        print("---")
        print("Flight:", flight.flight_number)
        print("Origin:", flight.origin_city, flight.origin_iata)
        print("Status:", flight.status)
        print("Arrival:", flight.effective_arrival)
        print("Terminal:", flight.terminal)


if __name__ == "__main__":
    asyncio.run(main())
