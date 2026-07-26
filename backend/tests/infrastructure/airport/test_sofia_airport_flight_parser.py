from datetime import datetime
from zoneinfo import ZoneInfo

from app.domain.flight_status import FlightStatus
from app.infrastructure.mappers import SofiaAirportFlightParser


SOFIA_TIMEZONE = ZoneInfo("Europe/Sofia")


def test_parser_reads_landed_flight() -> None:
    html = """
    <table>
        <tr
            data-airline='{"name":"WIZZ AIR"}'
            data-flight='{
                "ad":"A",
                "f":"W64450Z",
                "d":"13/07/2026",
                "t":"00:10",
                "dest":"PRG",
                "an":"PRAGUE",
                "ter":"T1",
                "st_en":"Landed",
                "est":"00:04"
            }'
        ></tr>
    </table>
    """

    flights = SofiaAirportFlightParser().parse_arrivals(html)

    assert len(flights) == 1

    flight = flights[0]

    assert flight.flight_number == "W64450Z"
    assert flight.origin_city == "Prague"
    assert flight.origin_iata == "PRG"
    assert flight.airline == "WIZZ AIR"
    assert flight.terminal == "Terminal 1"
    assert flight.status == FlightStatus.LANDED

    assert flight.scheduled_arrival == datetime(
        2026,
        7,
        13,
        0,
        10,
        tzinfo=SOFIA_TIMEZONE,
    )

    assert flight.actual_arrival == datetime(
        2026,
        7,
        13,
        0,
        4,
        tzinfo=SOFIA_TIMEZONE,
    )


def test_parser_reads_expected_flight() -> None:
    html = """
    <table>
        <tr
            data-airline='{"name":"RYANAIR"}'
            data-flight='{
                "ad":"A",
                "f":"FR4382",
                "d":"13/07/2026",
                "t":"00:40",
                "dest":"BVA",
                "an":"PARIS",
                "ter":"T2",
                "st_en":"Expected",
                "est":"00:45"
            }'
        ></tr>
    </table>
    """

    flights = SofiaAirportFlightParser().parse_arrivals(html)

    assert len(flights) == 1

    flight = flights[0]

    assert flight.flight_number == "FR4382"
    assert flight.origin_city == "Paris"
    assert flight.origin_iata == "BVA"
    assert flight.airline == "RYANAIR"
    assert flight.terminal == "Terminal 2"
    assert flight.status == FlightStatus.EXPECTED
    assert flight.estimated_arrival is not None
    assert flight.delay_minutes == 5
    assert flight.is_delayed is True


def test_parser_skips_departures() -> None:
    html = """
    <table>
        <tr
            data-airline='{"name":"TEST AIR"}'
            data-flight='{
                "ad":"D",
                "f":"TA100",
                "d":"13/07/2026",
                "t":"12:00",
                "dest":"LHR",
                "an":"LONDON",
                "ter":"T2",
                "st_en":"Scheduled",
                "est":""
            }'
        ></tr>
    </table>
    """

    flights = SofiaAirportFlightParser().parse_arrivals(html)

    assert flights == []


def test_parser_skips_invalid_json() -> None:
    html = """
    <table>
        <tr data-flight="invalid-json"></tr>
    </table>
    """

    flights = SofiaAirportFlightParser().parse_arrivals(html)

    assert flights == []


def test_parser_reads_saved_real_fixture() -> None:
    fixture_path = "tests/fixtures/airport/sofia_airport_arrivals.html"

    with open(
        fixture_path,
        encoding="utf-8",
    ) as fixture:
        html = fixture.read()

    flights = SofiaAirportFlightParser().parse_arrivals(html)

    assert len(flights) > 0
    assert all(flight.flight_number for flight in flights)
    assert all(flight.origin_city for flight in flights)
