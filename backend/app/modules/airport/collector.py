from app.modules.common.base_collector import BaseCollector


class AirportCollector(BaseCollector):
    """
    Collector responsible for airport intelligence data.
    """

    async def collect(self):
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
            "arrivals": [],
            "departures": [],
        }

    async def process(self, data):
        """
        Transform airport data into TIP signals.
        """

        return {
            "type": "airport_activity",
            "airport": data["airport"],
            "arrivals": len(data["arrivals"]),
            "departures": len(data["departures"]),
        }

    async def save(self, data):
        """
        Temporary persistence placeholder.

        Later:
        Repository -> PostgreSQL
        """

        print(
            "Airport signal:",
            data
        )