from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.domain import TrainStatus
from app.infrastructure.mappers import (
    SofiaRailwayArrivalParser,
)


SOFIA_TIMEZONE = ZoneInfo("Europe/Sofia")
SERVICE_DATE = date(2026, 7, 17)


def test_parser_reads_scheduled_train() -> None:
    html = """
    <div
        class="timetableItem"
        data-delay="0"
        data-train="50200"
    >
        <div class="row">
            <div class="col-3 col-lg-2">
                05:10
                <br>
                <small></small>
            </div>

            <div class="col-9 col-lg-7">
                <div class="row">
                    <div class="col-12 col-lg-6">
                        <p>
                            <strong>Перник</strong>
                        </p>
                    </div>

                    <div class="col-6 col-lg-4">
                        <span
                            data-toggle="tooltip"
                            title="Крайградски пътнически влак"
                        >
                            КПВ&nbsp;50200
                        </span>
                    </div>

                    <div data-station-id="160002"></div>
                </div>
            </div>

            <div class="col-12 col-lg-3"></div>
        </div>
    </div>
    """

    arrivals = SofiaRailwayArrivalParser().parse_arrivals(
        html,
        service_date=SERVICE_DATE,
    )

    assert len(arrivals) == 1

    arrival = arrivals[0]

    assert arrival.train_number == "50200"
    assert arrival.train_type_code == "КПВ"
    assert arrival.train_type_name == ("Крайградски пътнически влак")
    assert arrival.origin_station == "Перник"
    assert arrival.status == TrainStatus.SCHEDULED
    assert arrival.delay_minutes == 0
    assert arrival.platform is None
    assert arrival.expected_arrival is None

    assert arrival.scheduled_arrival == datetime(
        2026,
        7,
        17,
        5,
        10,
        tzinfo=SOFIA_TIMEZONE,
    )


def test_parser_reads_delayed_train() -> None:
    html = """
    <div
        class="timetableItem"
        data-delay="33"
        data-train="2626"
    >
        <div class="row">
            <div class="col-3 col-lg-2">
                <s>05:45</s>
                <br>
                06:18
                <br>
                <small></small>
            </div>

            <div class="col-9 col-lg-7">
                <div class="row">
                    <div>
                        <p>
                            <strong>Варна</strong>
                        </p>
                    </div>

                    <div>
                        <span
                            data-toggle="tooltip"
                            title="Бърз влак"
                        >
                            БВ&nbsp;2626
                        </span>
                    </div>

                    <div data-station-id="160002"></div>
                </div>
            </div>

            <div class="col-12 col-lg-3">
                Закъснение <strong>33</strong> мин.
            </div>
        </div>
    </div>
    """

    arrivals = SofiaRailwayArrivalParser().parse_arrivals(
        html,
        service_date=SERVICE_DATE,
    )

    assert len(arrivals) == 1

    arrival = arrivals[0]

    assert arrival.train_number == "2626"
    assert arrival.train_type_code == "БВ"
    assert arrival.origin_station == "Варна"
    assert arrival.status == TrainStatus.DELAYED
    assert arrival.delay_minutes == 33
    assert arrival.is_delayed is True

    assert arrival.scheduled_arrival == datetime(
        2026,
        7,
        17,
        5,
        45,
        tzinfo=SOFIA_TIMEZONE,
    )

    assert arrival.expected_arrival == datetime(
        2026,
        7,
        17,
        6,
        18,
        tzinfo=SOFIA_TIMEZONE,
    )

    assert arrival.effective_arrival == (arrival.expected_arrival)


def test_parser_reads_early_train() -> None:
    html = """
    <div
        class="timetableItem"
        data-delay="-2"
        data-train="3636"
    >
        <div class="row">
            <div>06:07</div>

            <div>
                <p>
                    <strong>Варна</strong>
                </p>

                <span
                    data-toggle="tooltip"
                    title="Бърз влак"
                >
                    БВ&nbsp;3636
                </span>

                <div data-station-id="160002"></div>
            </div>

            <div></div>
        </div>
    </div>
    """

    arrivals = SofiaRailwayArrivalParser().parse_arrivals(
        html,
        service_date=SERVICE_DATE,
    )

    assert len(arrivals) == 1

    arrival = arrivals[0]

    assert arrival.status == TrainStatus.EARLY
    assert arrival.delay_minutes == -2
    assert arrival.is_early is True
    assert arrival.is_delayed is False


def test_parser_skips_invalid_train_number() -> None:
    html = """
    <div
        class="timetableItem"
        data-delay="0"
        data-train="1234"
    >
        <div class="row">
            <div>10:00</div>

            <div>
                <p>
                    <strong>Пловдив</strong>
                </p>

                <span
                    data-toggle="tooltip"
                    title="Бърз влак"
                >
                    БВ&nbsp;9999
                </span>
            </div>

            <div></div>
        </div>
    </div>
    """

    arrivals = SofiaRailwayArrivalParser().parse_arrivals(
        html,
        service_date=SERVICE_DATE,
    )

    assert arrivals == []


def test_parser_skips_item_without_time() -> None:
    html = """
    <div
        class="timetableItem"
        data-delay="0"
        data-train="1234"
    >
        <div class="row">
            <div>unknown</div>

            <div>
                <p>
                    <strong>Пловдив</strong>
                </p>

                <span
                    data-toggle="tooltip"
                    title="Бърз влак"
                >
                    БВ&nbsp;1234
                </span>
            </div>

            <div></div>
        </div>
    </div>
    """

    arrivals = SofiaRailwayArrivalParser().parse_arrivals(
        html,
        service_date=SERVICE_DATE,
    )

    assert arrivals == []


def test_parser_reads_saved_real_fixture() -> None:
    fixture_path = "tests/fixtures/railway/sofia_railway_arrivals.html"

    with open(
        fixture_path,
        encoding="utf-8",
    ) as fixture:
        html = fixture.read()

    arrivals = SofiaRailwayArrivalParser().parse_arrivals(
        html,
        service_date=SERVICE_DATE,
    )

    assert len(arrivals) > 0

    assert all(arrival.train_number for arrival in arrivals)
    assert all(arrival.origin_station for arrival in arrivals)
    assert all(arrival.train_type_code for arrival in arrivals)
