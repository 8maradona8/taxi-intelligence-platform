import asyncio

from app.infrastructure.clients import SofiaAirportWebsiteClient
from app.infrastructure.http import AsyncHttpClient


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
        airport_client = SofiaAirportWebsiteClient(
            http_client=http_client,
        )

        arrivals_html = await airport_client.get_arrivals_html()

        print("Sofia Airport arrivals downloaded")
        print("HTML length:", len(arrivals_html))
        print("Contains Arrivals:", "Arrivals" in arrivals_html)
        print("Contains Sofia Airport:", "Sofia Airport" in arrivals_html)


if __name__ == "__main__":
    asyncio.run(main())
