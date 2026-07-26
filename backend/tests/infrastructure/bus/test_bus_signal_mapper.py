from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.domain import BusArrival
from app.domain.enums import (
    PriorityLevel,
    SignalSource,
    SignalType,
)
from app.infrastructure.mappers import (
    BusSignalMapper,
)


SOFIA_TIMEZONE = ZoneInfo("Europe/Sofia")


def make_arrival(
    *,
    origin: str,
    minutes_from_now: int,
    observed_at: datetime,
    carrier: str = "TEST CARRIER",
    sector: str | None = None,
) -> BusArrival:
    return BusArrival(
        origin=origin,
        route=f"{origin} - СОФИЯ",
        full_route=f"{origin} - СОФИЯ",
        carrier=carrier,
        scheduled_arrival=(observed_at + timedelta(minutes=minutes_from_now)),
        operating_days=(
            "пн",
            "вт",
            "ср",
            "чт",
            "пк",
            "сб",
            "нд",
        ),
        sector=sector,
    )


def test_mapper_creates_bus_signal() -> None:
    observed_at = datetime(
        2026,
        7,
        20,
        10,
        0,
        tzinfo=SOFIA_TIMEZONE,
    )

    arrivals = [
        make_arrival(
            origin="ВАРНА",
            minutes_from_now=20,
            observed_at=observed_at,
            carrier="ГЛОБАЛ БИОМЕТ ЕООД",
            sector="12",
        ),
        make_arrival(
            origin="ДОБРИЧ",
            minutes_from_now=40,
            observed_at=observed_at,
            carrier="ЮНИОН - ИВКОНИ ООД",
        ),
        make_arrival(
            origin="ВАРНА",
            minutes_from_now=60,
            observed_at=observed_at,
            carrier="ГЛОБАЛ БИОМЕТ ЕООД",
        ),
    ]

    signal = BusSignalMapper().map_arrivals(
        arrivals,
        observed_at=observed_at,
    )

    assert signal.source == (SignalSource.TRANSPORT)
    assert signal.signal_type == (SignalType.TRANSPORT_ACTIVITY)
    assert signal.zone_name == ("Sofia Central Bus Station")

    assert signal.payload["mode"] == "bus"
    assert signal.payload["station_code"] == ("sofia-central-bus-station")
    assert signal.payload["forecast_window_minutes"] == 120

    assert signal.payload["arrivals"] == 3
    assert signal.payload["unique_origins"] == 2
    assert signal.payload["known_sectors"] == 1

    assert signal.payload["origins"] == [
        "ВАРНА",
        "ДОБРИЧ",
    ]

    assert signal.payload["carriers"] == [
        "ГЛОБАЛ БИОМЕТ ЕООД",
        "ЮНИОН - ИВКОНИ ООД",
    ]

    assert signal.payload["carrier_distribution"] == {
        "ГЛОБАЛ БИОМЕТ ЕООД": 2,
        "ЮНИОН - ИВКОНИ ООД": 1,
    }

    assert signal.payload["sector_distribution"] == {
        "12": 1,
        "Unknown": 2,
    }

    assert signal.payload["routes"] == [
        "ВАРНА - СОФИЯ",
        "ДОБРИЧ - СОФИЯ",
        "ВАРНА - СОФИЯ",
    ]

    assert len(signal.payload["arrival_times"]) == 3

    assert signal.impact_score.value == 38.0
    assert signal.confidence.value == 0.95
    assert signal.priority == (PriorityLevel.LOW)


def test_mapper_ignores_arrivals_outside_window() -> None:
    observed_at = datetime(
        2026,
        7,
        20,
        10,
        0,
        tzinfo=SOFIA_TIMEZONE,
    )

    arrivals = [
        make_arrival(
            origin="ВАРНА",
            minutes_from_now=30,
            observed_at=observed_at,
        ),
        make_arrival(
            origin="ПЛОВДИВ",
            minutes_from_now=180,
            observed_at=observed_at,
        ),
    ]

    signal = BusSignalMapper().map_arrivals(
        arrivals,
        observed_at=observed_at,
    )

    assert signal.payload["arrivals"] == 1
    assert signal.payload["origins"] == [
        "ВАРНА",
    ]
    assert signal.payload["routes"] == [
        "ВАРНА - СОФИЯ",
    ]
    assert signal.impact_score.value == 13.0


def test_mapper_returns_empty_signal() -> None:
    observed_at = datetime(
        2026,
        7,
        20,
        10,
        0,
        tzinfo=SOFIA_TIMEZONE,
    )

    signal = BusSignalMapper().map_arrivals(
        [],
        observed_at=observed_at,
    )

    assert signal.payload["arrivals"] == 0
    assert signal.payload["unique_origins"] == 0
    assert signal.payload["known_sectors"] == 0
    assert signal.payload["origins"] == []
    assert signal.payload["carriers"] == []
    assert signal.payload["carrier_distribution"] == {}
    assert signal.payload["sector_distribution"] == {}
    assert signal.payload["arrival_times"] == []
    assert signal.payload["routes"] == []

    assert signal.impact_score.value == 0.0
    assert signal.confidence.value == 0.50
    assert signal.priority == (PriorityLevel.LOW)


def test_mapper_caps_impact_score_at_100() -> None:
    observed_at = datetime(
        2026,
        7,
        20,
        10,
        0,
        tzinfo=SOFIA_TIMEZONE,
    )

    arrivals = [
        make_arrival(
            origin=f"ORIGIN {index}",
            minutes_from_now=index * 5,
            observed_at=observed_at,
            sector=str(index),
        )
        for index in range(
            1,
            10,
        )
    ]

    signal = BusSignalMapper().map_arrivals(
        arrivals,
        observed_at=observed_at,
    )

    assert signal.impact_score.value == 100.0
    assert signal.priority == (PriorityLevel.HIGH)


def test_mapper_assigns_medium_priority() -> None:
    observed_at = datetime(
        2026,
        7,
        20,
        10,
        0,
        tzinfo=SOFIA_TIMEZONE,
    )

    arrivals = [
        make_arrival(
            origin=f"ORIGIN {index}",
            minutes_from_now=index * 10,
            observed_at=observed_at,
        )
        for index in range(
            1,
            5,
        )
    ]

    signal = BusSignalMapper().map_arrivals(
        arrivals,
        observed_at=observed_at,
    )

    assert signal.impact_score.value == 52.0
    assert signal.priority == (PriorityLevel.MEDIUM)


def test_mapper_rejects_invalid_configuration() -> None:
    invalid_configurations = [
        {
            "forecast_window": timedelta(0),
            "message": ("forecast_window must be positive"),
        },
        {
            "signal_ttl": timedelta(0),
            "message": ("signal_ttl must be positive"),
        },
        {
            "zone_name": " ",
            "message": ("zone_name cannot be empty"),
        },
        {
            "station_code": " ",
            "message": ("station_code cannot be empty"),
        },
    ]

    for configuration in invalid_configurations:
        expected_message = str(configuration.pop("message"))

        try:
            BusSignalMapper(
                **configuration,
            )
        except ValueError as exc:
            assert str(exc) == (expected_message)
        else:
            raise AssertionError("Expected ValueError")
