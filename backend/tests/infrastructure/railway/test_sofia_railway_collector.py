from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from app.domain import TrainArrival, TrainStatus
from app.infrastructure.collectors import (
    SofiaRailwayCollector,
)


SOFIA_TIMEZONE = ZoneInfo("Europe/Sofia")


class FakeRailwayClient:
    async def get_sofia_arrivals_html(self) -> str:
        return "<html>railway-data</html>"


class FakeRailwayParser:
    def parse_arrivals(
        self,
        html: str,
        *,
        service_date: date,
    ) -> list[TrainArrival]:
        assert html == "<html>railway-data</html>"
        assert service_date == date(2026, 7, 17)

        return [
            TrainArrival(
                train_number="2626",
                train_type_code="БВ",
                train_type_name="Бърз влак",
                origin_station="Варна",
                scheduled_arrival=datetime(
                    2026,
                    7,
                    17,
                    5,
                    45,
                    tzinfo=SOFIA_TIMEZONE,
                ),
                expected_arrival=datetime(
                    2026,
                    7,
                    17,
                    6,
                    18,
                    tzinfo=SOFIA_TIMEZONE,
                ),
                delay_minutes=33,
                status=TrainStatus.DELAYED,
            )
        ]


@pytest.mark.anyio
async def test_collector_returns_parsed_arrivals() -> None:
    collector = SofiaRailwayCollector(
        client=FakeRailwayClient(),  # type: ignore[arg-type]
        parser=FakeRailwayParser(),  # type: ignore[arg-type]
    )

    arrivals = await collector.collect_arrivals(
        service_date=date(2026, 7, 17),
    )

    assert len(arrivals) == 1

    arrival = arrivals[0]

    assert arrival.train_number == "2626"
    assert arrival.origin_station == "Варна"
    assert arrival.status == TrainStatus.DELAYED
    assert arrival.delay_minutes == 33
