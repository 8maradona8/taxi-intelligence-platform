from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.domain import TrainArrival, TrainStatus
from app.domain.enums import (
    PriorityLevel,
    SignalSource,
    SignalType,
)
from app.infrastructure.mappers import (
    RailwaySignalMapper,
)


SOFIA_TIMEZONE = ZoneInfo("Europe/Sofia")


def make_arrival(
    *,
    number: str,
    minutes_from_now: int,
    observed_at: datetime,
    status: TrainStatus,
    train_type_code: str = "КПВ",
    train_type_name: str = ("Крайградски пътнически влак"),
    delay_minutes: int = 0,
    platform: str | None = None,
) -> TrainArrival:
    scheduled_arrival = observed_at + timedelta(minutes=minutes_from_now)

    expected_arrival = None

    if delay_minutes != 0:
        expected_arrival = scheduled_arrival + timedelta(minutes=delay_minutes)

    return TrainArrival(
        train_number=number,
        train_type_code=train_type_code,
        train_type_name=train_type_name,
        origin_station="Test Station",
        scheduled_arrival=scheduled_arrival,
        expected_arrival=expected_arrival,
        delay_minutes=delay_minutes,
        platform=platform,
        status=status,
    )


def test_mapper_creates_railway_signal() -> None:
    observed_at = datetime(
        2026,
        7,
        17,
        10,
        0,
        tzinfo=SOFIA_TIMEZONE,
    )

    arrivals = [
        make_arrival(
            number="50200",
            minutes_from_now=20,
            observed_at=observed_at,
            status=TrainStatus.SCHEDULED,
            platform="1",
        ),
        make_arrival(
            number="2626",
            minutes_from_now=40,
            observed_at=observed_at,
            status=TrainStatus.DELAYED,
            train_type_code="БВ",
            train_type_name="Бърз влак",
            delay_minutes=20,
            platform="3",
        ),
        make_arrival(
            number="3636",
            minutes_from_now=60,
            observed_at=observed_at,
            status=TrainStatus.EARLY,
            train_type_code="БВ",
            train_type_name="Бърз влак",
            delay_minutes=-2,
            platform="3",
        ),
    ]

    signal = RailwaySignalMapper().map_arrivals(
        arrivals,
        observed_at=observed_at,
    )

    assert signal.source == (SignalSource.TRANSPORT)
    assert signal.signal_type == (SignalType.TRANSPORT_ACTIVITY)
    assert signal.zone_name == ("Sofia Central Railway Station")

    assert signal.payload["mode"] == "railway"
    assert signal.payload["station_code"] == ("sofia-central")
    assert signal.payload["arrivals"] == 3
    assert signal.payload["scheduled"] == 1
    assert signal.payload["expected"] == 0
    assert signal.payload["delayed"] == 1
    assert signal.payload["early"] == 1
    assert signal.payload["total_positive_delay_minutes"] == 20

    assert signal.payload["train_type_distribution"] == {
        "КПВ": 1,
        "БВ": 2,
    }

    assert signal.payload["platform_distribution"] == {
        "1": 1,
        "3": 2,
    }

    assert signal.payload["train_numbers"] == [
        "50200",
        "2626",
        "3636",
    ]

    assert signal.impact_score.value == 52.0
    assert signal.confidence.value == 0.95
    assert signal.priority == (PriorityLevel.MEDIUM)


def test_mapper_ignores_arrivals_outside_window() -> None:
    observed_at = datetime(
        2026,
        7,
        17,
        10,
        0,
        tzinfo=SOFIA_TIMEZONE,
    )

    arrivals = [
        make_arrival(
            number="50200",
            minutes_from_now=30,
            observed_at=observed_at,
            status=TrainStatus.SCHEDULED,
        ),
        make_arrival(
            number="50202",
            minutes_from_now=180,
            observed_at=observed_at,
            status=TrainStatus.SCHEDULED,
        ),
    ]

    signal = RailwaySignalMapper().map_arrivals(
        arrivals,
        observed_at=observed_at,
    )

    assert signal.payload["arrivals"] == 1
    assert signal.payload["train_numbers"] == [
        "50200",
    ]
    assert signal.impact_score.value == 10.0


def test_mapper_ignores_cancelled_arrivals() -> None:
    observed_at = datetime(
        2026,
        7,
        17,
        10,
        0,
        tzinfo=SOFIA_TIMEZONE,
    )

    arrivals = [
        make_arrival(
            number="2626",
            minutes_from_now=30,
            observed_at=observed_at,
            status=TrainStatus.CANCELLED,
            train_type_code="БВ",
            train_type_name="Бърз влак",
        )
    ]

    signal = RailwaySignalMapper().map_arrivals(
        arrivals,
        observed_at=observed_at,
    )

    assert signal.payload["arrivals"] == 0
    assert signal.payload["train_numbers"] == []
    assert signal.impact_score.value == 0.0
    assert signal.confidence.value == 0.50
    assert signal.priority == PriorityLevel.LOW


def test_mapper_caps_impact_score_at_100() -> None:
    observed_at = datetime(
        2026,
        7,
        17,
        10,
        0,
        tzinfo=SOFIA_TIMEZONE,
    )

    arrivals = [
        make_arrival(
            number=str(2600 + index),
            minutes_from_now=index * 5,
            observed_at=observed_at,
            status=TrainStatus.DELAYED,
            train_type_code="БВ",
            train_type_name="Бърз влак",
            delay_minutes=30,
        )
        for index in range(1, 10)
    ]

    signal = RailwaySignalMapper().map_arrivals(
        arrivals,
        observed_at=observed_at,
    )

    assert signal.impact_score.value == 100.0
    assert signal.priority == PriorityLevel.HIGH


def test_mapper_rejects_invalid_configuration() -> None:
    try:
        RailwaySignalMapper(
            forecast_window=timedelta(0),
        )
    except ValueError as exc:
        assert str(exc) == ("forecast_window must be positive")
    else:
        raise AssertionError("Expected ValueError")
