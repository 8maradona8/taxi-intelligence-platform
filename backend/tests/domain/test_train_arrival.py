from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.domain import TrainArrival, TrainStatus


SOFIA_TIMEZONE = ZoneInfo("Europe/Sofia")


def make_train_arrival(
    **overrides: object,
) -> TrainArrival:
    values: dict[str, object] = {
        "train_number": "2626",
        "train_type_code": "БВ",
        "train_type_name": "Бърз влак",
        "origin_station": "Варна",
        "scheduled_arrival": datetime(
            2026,
            7,
            17,
            5,
            45,
            tzinfo=SOFIA_TIMEZONE,
        ),
        "status": TrainStatus.SCHEDULED,
    }

    values.update(overrides)

    return TrainArrival(**values)  # type: ignore[arg-type]


def test_train_arrival_normalizes_values() -> None:
    arrival = make_train_arrival(
        train_number=" 2626 ",
        train_type_code=" бв ",
        train_type_name=" Бърз влак ",
        origin_station=" Варна ",
        platform=" 3 ",
    )

    assert arrival.train_number == "2626"
    assert arrival.train_type_code == "БВ"
    assert arrival.train_type_name == "Бърз влак"
    assert arrival.origin_station == "Варна"
    assert arrival.platform == "3"


def test_train_arrival_rejects_empty_number() -> None:
    with pytest.raises(
        ValueError,
        match="train_number cannot be empty",
    ):
        make_train_arrival(
            train_number=" ",
        )


def test_delayed_arrival_is_detected() -> None:
    arrival = make_train_arrival(
        status=TrainStatus.DELAYED,
        delay_minutes=33,
    )

    assert arrival.is_delayed is True
    assert arrival.is_early is False


def test_early_arrival_is_detected() -> None:
    arrival = make_train_arrival(
        status=TrainStatus.EARLY,
        delay_minutes=-2,
    )

    assert arrival.is_early is True
    assert arrival.is_delayed is False
