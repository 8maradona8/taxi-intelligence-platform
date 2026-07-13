import asyncio

from app.database.session import AsyncSessionLocal
from app.repositories import SignalRepository, ZoneRepository
from app.services.airport_signal_history_service import (
    AirportSignalHistoryService,
)


async def main() -> None:
    async with AsyncSessionLocal() as session:
        service = AirportSignalHistoryService(
            zone_repository=ZoneRepository(session),
            signal_repository=SignalRepository(session),
        )

        signals = await service.get_history(
            limit=10,
        )

        print("Airport signals:", len(signals))

        for signal in signals:
            print("---")
            print("ID:", signal.id)
            print("Impact:", signal.impact_score)
            print("Observed at:", signal.observed_at)
            print(
                "Arrivals:",
                signal.payload.get("arrivals"),
            )
            print(
                "Flights:",
                signal.payload.get("flight_numbers"),
            )


if __name__ == "__main__":
    asyncio.run(main())
