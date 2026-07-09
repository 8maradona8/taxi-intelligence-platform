import asyncio

from app.database.session import AsyncSessionLocal
from app.services.airport_service import AirportService


async def main() -> None:
    async with AsyncSessionLocal() as session:
        airport_service = AirportService(session)

        signal = await airport_service.create_airport_activity_signal(
            airport_code="SOF",
            arrivals=3,
            departures=1,
        )

        print(f"Created airport signal ID: {signal.id}")
        print(f"Impact score: {signal.impact_score}")


if __name__ == "__main__":
    asyncio.run(main())