import asyncio

from app.modules.airport.collector import AirportCollector


async def main():

    collector = AirportCollector()

    await collector.run()


if __name__ == "__main__":
    asyncio.run(main())