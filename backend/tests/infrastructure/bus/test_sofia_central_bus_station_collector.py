from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.domain import BusArrival
from app.infrastructure.collectors import (
    SofiaCentralBusStationCollector,
)


SOFIA_TIMEZONE = ZoneInfo("Europe/Sofia")


class FakeBusClient:
    ALLOWED_HORIZON_HOURS = {
        1,
        2,
        4,
        8,
        12,
    }

    def __init__(self) -> None:
        self.received_hours: int | None = None

    async def get_arrivals_html(
        self,
        *,
        hours: int = 2,
    ) -> str:
        self.received_hours = hours

        return "<html>bus-data</html>"


class FakeBusParser:
    def __init__(self) -> None:
        self.received_html: str | None = None
        self.received_observed_at: datetime | None = None

    def parse_arrivals(
        self,
        html: str,
        *,
        observed_at: datetime | None = None,
    ) -> list[BusArrival]:
        self.received_html = html
        self.received_observed_at = observed_at

        return [
            BusArrival(
                origin="ВАРНА",
                route="ВАРНА - СОФИЯ",
                full_route=("ВАРНА - В.ТЪРНОВО - СОФИЯ"),
                carrier="ГЛОБАЛ БИОМЕТ EООД",
                scheduled_arrival=datetime(
                    2026,
                    7,
                    20,
                    23,
                    51,
                    tzinfo=SOFIA_TIMEZONE,
                ),
                operating_days=(
                    "пн",
                    "вт",
                    "ср",
                    "чт",
                    "пк",
                    "сб",
                    "нд",
                ),
            )
        ]


@pytest.mark.anyio
async def test_collector_returns_parsed_arrivals() -> None:
    observed_at = datetime(
        2026,
        7,
        20,
        22,
        0,
        tzinfo=SOFIA_TIMEZONE,
    )

    client = FakeBusClient()
    parser = FakeBusParser()

    collector = SofiaCentralBusStationCollector(
        client=client,  # type: ignore[arg-type]
        parser=parser,  # type: ignore[arg-type]
        horizon_hours=2,
    )

    arrivals = await collector.collect_arrivals(
        observed_at=observed_at,
    )

    assert client.received_hours == 2
    assert parser.received_html == ("<html>bus-data</html>")
    assert parser.received_observed_at == observed_at

    assert len(arrivals) == 1

    arrival = arrivals[0]

    assert arrival.origin == "ВАРНА"
    assert arrival.route == "ВАРНА - СОФИЯ"
    assert arrival.carrier == ("ГЛОБАЛ БИОМЕТ EООД")


@pytest.mark.anyio
async def test_collector_uses_configured_horizon() -> None:
    client = FakeBusClient()
    parser = FakeBusParser()

    collector = SofiaCentralBusStationCollector(
        client=client,  # type: ignore[arg-type]
        parser=parser,  # type: ignore[arg-type]
        horizon_hours=4,
    )

    await collector.collect_arrivals()

    assert client.received_hours == 4


def test_collector_rejects_unsupported_horizon() -> None:
    client = FakeBusClient()
    parser = FakeBusParser()

    with pytest.raises(
        ValueError,
        match="horizon_hours must be one of",
    ):
        SofiaCentralBusStationCollector(
            client=client,  # type: ignore[arg-type]
            parser=parser,  # type: ignore[arg-type]
            horizon_hours=3,
        )
