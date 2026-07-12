from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.domain.enums import (
    PriorityLevel,
    SignalSource,
    SignalType,
)
from app.domain.flight import Flight
from app.domain.flight_status import FlightStatus
from app.infrastructure.mappers import AirportSignalMapper


SOFIA_TIMEZONE = ZoneInfo("Europe/Sofia")


def make_flight(
    *,
    number: str,
    minutes_from_now: int,
    status: FlightStatus,
    observed_at: datetime,
    terminal: str = "Terminal 2",
) -> Flight:
    scheduled_arrival = observed_at + timedelta(minutes=minutes_from_now)

    return Flight(
        flight_number=number,
        origin_city="Test City",
        origin_iata="TST",
        scheduled_arrival=scheduled_arrival,
        status=status,
        terminal=terminal,
    )


def test_mapper_creates_airport_signal() -> None:
    observed_at = datetime(
        2026,
        7,
        13,
        10,
        0,
        tzinfo=SOFIA_TIMEZONE,
    )

    flights = [
        make_flight(
            number="FR100",
            minutes_from_now=20,
            status=FlightStatus.SCHEDULED,
            observed_at=observed_at,
        ),
        make_flight(
            number="W6100",
            minutes_from_now=40,
            status=FlightStatus.EXPECTED,
            observed_at=observed_at,
        ),
        make_flight(
            number="LH100",
            minutes_from_now=60,
            status=FlightStatus.DELAYED,
            observed_at=observed_at,
            terminal="Terminal 1",
        ),
    ]

    signal = AirportSignalMapper().map_arrivals(
        flights,
        observed_at=observed_at,
    )

    assert signal.source == SignalSource.AIRPORT
    assert signal.signal_type == SignalType.AIRPORT_ACTIVITY
    assert signal.zone_name == "Sofia Airport"

    assert signal.payload["arrivals"] == 3
    assert signal.payload["scheduled"] == 1
    assert signal.payload["expected"] == 1
    assert signal.payload["delayed"] == 1
    assert signal.payload["cancelled"] == 0

    assert signal.payload["terminal_distribution"] == {
        "Terminal 2": 2,
        "Terminal 1": 1,
    }

    assert signal.impact_score.value == 44.0
    assert signal.confidence.value == 0.95
    assert signal.priority == PriorityLevel.MEDIUM


def test_mapper_ignores_flights_outside_window() -> None:
    observed_at = datetime(
        2026,
        7,
        13,
        10,
        0,
        tzinfo=SOFIA_TIMEZONE,
    )

    flights = [
        make_flight(
            number="FR100",
            minutes_from_now=30,
            status=FlightStatus.SCHEDULED,
            observed_at=observed_at,
        ),
        make_flight(
            number="FR200",
            minutes_from_now=180,
            status=FlightStatus.SCHEDULED,
            observed_at=observed_at,
        ),
    ]

    signal = AirportSignalMapper().map_arrivals(
        flights,
        observed_at=observed_at,
    )

    assert signal.payload["arrivals"] == 1
    assert signal.payload["flight_numbers"] == [
        "FR100",
    ]
    assert signal.impact_score.value == 12.0


def test_mapper_ignores_cancelled_flights() -> None:
    observed_at = datetime(
        2026,
        7,
        13,
        10,
        0,
        tzinfo=SOFIA_TIMEZONE,
    )

    flights = [
        make_flight(
            number="FR100",
            minutes_from_now=30,
            status=FlightStatus.CANCELLED,
            observed_at=observed_at,
        )
    ]

    signal = AirportSignalMapper().map_arrivals(
        flights,
        observed_at=observed_at,
    )

    assert signal.payload["arrivals"] == 0
    assert signal.payload["cancelled"] == 0
    assert signal.impact_score.value == 0.0
    assert signal.confidence.value == 0.50
    assert signal.priority == PriorityLevel.LOW


def test_mapper_caps_impact_score_at_100() -> None:
    observed_at = datetime(
        2026,
        7,
        13,
        10,
        0,
        tzinfo=SOFIA_TIMEZONE,
    )

    flights = [
        make_flight(
            number=f"FR{index}",
            minutes_from_now=index * 5,
            status=FlightStatus.DELAYED,
            observed_at=observed_at,
        )
        for index in range(1, 10)
    ]

    signal = AirportSignalMapper().map_arrivals(
        flights,
        observed_at=observed_at,
    )

    assert signal.impact_score.value == 100.0
    assert signal.priority == PriorityLevel.HIGH
