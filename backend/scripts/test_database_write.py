import asyncio
from datetime import UTC, datetime

from app.database.session import AsyncSessionLocal
from app.repositories.signal_repository import SignalRepository
from app.repositories.zone_repository import ZoneRepository


async def main() -> None:
    async with AsyncSessionLocal() as session:
        zone_repository = ZoneRepository(session)
        signal_repository = SignalRepository(session)

        zone = await zone_repository.get_by_name("Sofia Airport")

        if zone is None:
            zone = await zone_repository.create(
                name="Sofia Airport",
                city="Sofia",
                country="Bulgaria",
                latitude=42.6967,
                longitude=23.4114,
            )

        signal = await signal_repository.create(
            signal_type="airport_activity",
            source="airport_collector",
            zone_id=zone.id,
            impact_score=25.0,
            observed_at=datetime.now(UTC),
            payload={
                "airport": "SOF",
                "arrivals": 0,
                "departures": 0,
            },
        )

        print(f"Created signal ID: {signal.id}")
        print(f"Zone: {zone.name}")


if __name__ == "__main__":
    asyncio.run(main())