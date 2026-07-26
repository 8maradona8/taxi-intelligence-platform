from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.domain.flight import Flight
from app.domain.flight_status import FlightStatus
from app.infrastructure.collectors import SofiaAirportCollector


SOFIA_TIMEZONE = ZoneInfo("Europe/Sofia")


class FakeAirportClient:
    async def get_arrivals_html(self) -> str:
        return "<html>airport-data</html>"


class FakeAirportParser:
    def parse_arrivals(
        self,
        html: str,
    ) -> list[Flight]:
        assert html == "<html>airport-data</html>"

        return [
            Flight(
                flight_number="FR4382",
                origin_city="Paris",
                origin_iata="BVA",
                scheduled_arrival=datetime(
                    2026,
                    7,
                    13,
                    0,
                    40,
                    tzinfo=SOFIA_TIMEZONE,
                ),
                status=FlightStatus.EXPECTED,
                terminal="Terminal 2",
                airline="RYANAIR",
            )
        ]


@pytest.mark.anyio
async def test_collector_returns_parsed_arrivals() -> None:
    collector = SofiaAirportCollector(
        client=FakeAirportClient(),
        parser=FakeAirportParser(),
    )

    flights = await collector.collect_arrivals()

    assert len(flights) == 1
    assert flights[0].flight_number == "FR4382"
    assert flights[0].origin_city == "Paris"
    assert flights[0].status == FlightStatus.EXPECTED
