from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.infrastructure.mappers import (
    SofiaCentralBusArrivalParser,
)


SOFIA_TIMEZONE = ZoneInfo("Europe/Sofia")


def test_parser_reads_bus_arrival() -> None:
    html = """
    <div id="results_container">
        <table class="result_table_odd" width="100%">
            <tr>
                <td>
                    ВАРНА - СОФИЯ
                    Валиден от 2022-12-31
                    Валиден до 2026-12-31
                </td>
                <td>ГЛОБАЛ БИОМЕТ EООД</td>
                <td>пн вт ср чт пк сб нд</td>
                <td>23:51ч.</td>
                <td>Сектор 12</td>
                <td></td>
            </tr>
            <tr>
                <td
                    colspan="6"
                    class="sr_full_route"
                >
                    ВАРНА - В.ТЪРНОВО - СОФИЯ
                </td>
            </tr>
        </table>
    </div>
    """

    observed_at = datetime(
        2026,
        7,
        19,
        23,
        40,
        tzinfo=SOFIA_TIMEZONE,
    )

    arrivals = SofiaCentralBusArrivalParser().parse_arrivals(
        html,
        observed_at=observed_at,
    )

    assert len(arrivals) == 1

    arrival = arrivals[0]

    assert arrival.origin == "ВАРНА"
    assert arrival.route == "ВАРНА - СОФИЯ"
    assert arrival.full_route == ("ВАРНА - В.ТЪРНОВО - СОФИЯ")
    assert arrival.carrier == "ГЛОБАЛ БИОМЕТ EООД"
    assert arrival.operating_days == (
        "пн",
        "вт",
        "ср",
        "чт",
        "пк",
        "сб",
        "нд",
    )
    assert arrival.valid_from == date(
        2022,
        12,
        31,
    )
    assert arrival.valid_until == date(
        2026,
        12,
        31,
    )
    assert arrival.sector == "12"
    assert arrival.scheduled_arrival == datetime(
        2026,
        7,
        19,
        23,
        51,
        tzinfo=SOFIA_TIMEZONE,
    )


def test_parser_rolls_midnight_arrival_to_next_day() -> None:
    html = """
    <div id="results_container">
        <table class="result_table_even">
            <tr>
                <td>
                    ВАРНА - СОФИЯ
                    Валиден до 2026-12-31
                </td>
                <td>ГРУП ПЛЮС ООД</td>
                <td>пн вт ср чт пк сб нд</td>
                <td>00:00ч.</td>
                <td></td>
                <td></td>
            </tr>
            <tr>
                <td
                    colspan="6"
                    class="sr_full_route"
                >
                    ВАРНА - В.ТЪРНОВО - СОФИЯ
                </td>
            </tr>
        </table>
    </div>
    """

    observed_at = datetime(
        2026,
        7,
        19,
        23,
        40,
        tzinfo=SOFIA_TIMEZONE,
    )

    arrivals = SofiaCentralBusArrivalParser().parse_arrivals(
        html,
        observed_at=observed_at,
    )

    assert len(arrivals) == 1

    assert arrivals[0].scheduled_arrival == datetime(
        2026,
        7,
        20,
        0,
        0,
        tzinfo=SOFIA_TIMEZONE,
    )


def test_parser_uses_route_when_full_route_is_missing() -> None:
    html = """
    <div id="results_container">
        <table class="result_table_odd">
            <tr>
                <td>
                    ДОБРИЧ - СОФИЯ
                    Валиден до 2026-12-31
                </td>
                <td>ЮНИОН - ИВКОНИ ООД</td>
                <td>пн ср пк</td>
                <td>00:30ч.</td>
                <td></td>
                <td></td>
            </tr>
        </table>
    </div>
    """

    observed_at = datetime(
        2026,
        7,
        19,
        23,
        40,
        tzinfo=SOFIA_TIMEZONE,
    )

    arrivals = SofiaCentralBusArrivalParser().parse_arrivals(
        html,
        observed_at=observed_at,
    )

    assert len(arrivals) == 1

    arrival = arrivals[0]

    assert arrival.origin == "ДОБРИЧ"
    assert arrival.route == "ДОБРИЧ - СОФИЯ"
    assert arrival.full_route == "ДОБРИЧ - СОФИЯ"
    assert arrival.valid_from is None
    assert arrival.valid_until == date(
        2026,
        12,
        31,
    )
    assert arrival.sector is None


def test_parser_skips_invalid_rows() -> None:
    html = """
    <div id="results_container">
        <table class="result_table_odd">
            <tr>
                <td>ВАРНА - СОФИЯ</td>
                <td></td>
                <td>пн вт ср</td>
                <td>invalid-time</td>
            </tr>
        </table>
    </div>
    """

    arrivals = SofiaCentralBusArrivalParser().parse_arrivals(
        html,
        observed_at=datetime(
            2026,
            7,
            19,
            22,
            0,
            tzinfo=SOFIA_TIMEZONE,
        ),
    )

    assert arrivals == []


def test_parser_ignores_unrelated_tables() -> None:
    html = """
    <div id="results_container">
        <table class="results_title">
            <tr>
                <td>Маршрут</td>
                <td>Компания</td>
            </tr>
        </table>
    </div>

    <table id="pop-list">
        <tr>
            <td>ПЛОВДИВ</td>
            <td>8.50 EUR</td>
        </tr>
    </table>
    """

    arrivals = SofiaCentralBusArrivalParser().parse_arrivals(
        html,
        observed_at=datetime(
            2026,
            7,
            19,
            22,
            0,
            tzinfo=SOFIA_TIMEZONE,
        ),
    )

    assert arrivals == []


def test_parser_reads_saved_real_fixture() -> None:
    fixture_path = Path("tests/fixtures/bus/sofia_central_bus_arrivals_2h.html")

    html = fixture_path.read_text(
        encoding="utf-8",
    )

    arrivals = SofiaCentralBusArrivalParser().parse_arrivals(
        html,
        observed_at=datetime(
            2026,
            7,
            19,
            23,
            40,
            tzinfo=SOFIA_TIMEZONE,
        ),
    )

    assert len(arrivals) > 0

    assert all(arrival.origin for arrival in arrivals)
    assert all(arrival.route for arrival in arrivals)
    assert all(arrival.full_route for arrival in arrivals)
    assert all(arrival.carrier for arrival in arrivals)
    assert all(arrival.scheduled_arrival.tzinfo is not None for arrival in arrivals)
