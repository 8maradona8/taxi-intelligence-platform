from sqlalchemy.ext.asyncio import AsyncSession

from app.models.signal import Signal
from app.modules.common.base_collector import BaseCollector
from app.services.airport_service import AirportService


class AirportCollector(BaseCollector):
    """
    Collector responsible for airport intelligence data.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.airport_service = AirportService(session)

    async def collect(self) -> dict:
        """
        Fetch raw airport data.

        Later:
        - Sofia Airport API
        - FlightRadar API
        - AviationStack
        - OpenSky Network
        """

        return {
            "airport": "SOF",
            "arrivals": 3,
            "departures": 1,
        }

    async def process(self, data: dict) -> dict:
        """
        Transform raw airport data into service input.
        """

        return {
            "airport_code": data["airport"],
            "arrivals": data["arrivals"],
            "departures": data["departures"],
        }

    async def save(self, data: dict) -> Signal:
        """
        Persist airport activity as a TIP signal.
        """

        return await self.airport_service.create_airport_activity_signal(
            airport_code=data["airport_code"],
            arrivals=data["arrivals"],
            departures=data["departures"],
        )
