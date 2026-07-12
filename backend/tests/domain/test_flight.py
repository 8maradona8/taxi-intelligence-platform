from datetime import UTC, datetime, timedelta

import pytest

from app.domain.flight import Flight
from app.domain.flight_status import FlightStatus


def test_flight_normalizes_text_fields() -> None:
    flight = Flight(
        flight_number=" fr5642 ",
        origin_city=" Budapest ",
        origin_iata="bud",
        scheduled_arrival=datetime(
            2026,
            7,
            13,
            14,
            25,
            tzinfo=UTC,
        ),
        status=FlightStatus.SCHEDULED,
        airline=" Ryanair ",
        terminal=" Terminal 2 ",
    )

    assert flight.flight_number == "FR5642"
    assert flight.origin_city == "Budapest"
    assert flight.origin_iata == "BUD"
    assert flight.airline == "Ryanair"
    assert flight.terminal == "Terminal 2"


def test_flight_uses_estimated_arrival() -> None:
    scheduled = datetime(
        2026,
        7,
        13,
        14,
        25,
        tzinfo=UTC,
    )

    estimated = scheduled + timedelta(minutes=18)

    flight = Flight(
        flight_number="FR5642",
        origin_city="Budapest",
        origin_iata="BUD",
        scheduled_arrival=scheduled,
        estimated_arrival=estimated,
        status=FlightStatus.EXPECTED,
    )

    assert flight.effective_arrival == estimated
    assert flight.delay_minutes == 18
    assert flight.is_delayed is True


def test_actual_arrival_has_priority_over_estimated() -> None:
    scheduled = datetime(
        2026,
        7,
        13,
        14,
        25,
        tzinfo=UTC,
    )

    estimated = scheduled + timedelta(minutes=10)
    actual = scheduled + timedelta(minutes=14)

    flight = Flight(
        flight_number="FR5642",
        origin_city="Budapest",
        origin_iata="BUD",
        scheduled_arrival=scheduled,
        estimated_arrival=estimated,
        actual_arrival=actual,
        status=FlightStatus.LANDED,
    )

    assert flight.effective_arrival == actual
    assert flight.delay_minutes == 14


def test_cancelled_flight_is_identified() -> None:
    flight = Flight(
        flight_number="W64402",
        origin_city="Madrid",
        origin_iata="MAD",
        scheduled_arrival=datetime(
            2026,
            7,
            13,
            16,
            30,
            tzinfo=UTC,
        ),
        status=FlightStatus.CANCELLED,
    )

    assert flight.is_cancelled is True


def test_invalid_iata_code_raises_error() -> None:
    with pytest.raises(
        ValueError,
        match="origin_iata must contain exactly 3 characters",
    ):
        Flight(
            flight_number="FR5642",
            origin_city="Budapest",
            origin_iata="BU",
            scheduled_arrival=datetime(
                2026,
                7,
                13,
                14,
                25,
                tzinfo=UTC,
            ),
            status=FlightStatus.SCHEDULED,
        )
