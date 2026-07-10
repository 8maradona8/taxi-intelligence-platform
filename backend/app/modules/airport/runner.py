import asyncio

from app.database.session import AsyncSessionLocal
from app.modules.airport.collector import AirportCollector


async def main() -> None:
    async with AsyncSessionLocal() as session:
        collector = AirportCollector(session)

        signal = await collector.run()

        print(f"Airport collector created signal ID: {signal.id}")
        print(f"Impact score: {signal.impact_score}")


if __name__ == "__main__":
    asyncio.run(main())
