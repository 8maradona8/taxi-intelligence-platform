import pytest

from app.application.interfaces import (
    AIRPORT_SCHEDULER,
    BUS_SCHEDULER,
    RAILWAY_SCHEDULER,
    SchedulerIdentity,
)


def test_scheduler_identity_normalizes_key() -> None:
    identity = SchedulerIdentity(
        key="  WEATHER  ",
        name="weather-signal-scheduler",
    )

    assert identity.key == "weather"
    assert identity.name == ("weather-signal-scheduler")


def test_scheduler_identity_rejects_empty_key() -> None:
    with pytest.raises(
        ValueError,
        match="scheduler key cannot be empty",
    ):
        SchedulerIdentity(
            key=" ",
            name="weather-signal-scheduler",
        )


def test_scheduler_identity_rejects_empty_name() -> None:
    with pytest.raises(
        ValueError,
        match="scheduler name cannot be empty",
    ):
        SchedulerIdentity(
            key="weather",
            name=" ",
        )


def test_airport_scheduler_identity_is_stable() -> None:
    assert AIRPORT_SCHEDULER.key == "airport"
    assert AIRPORT_SCHEDULER.name == ("airport-signal-scheduler")


def test_bus_scheduler_identity_is_stable() -> None:
    assert BUS_SCHEDULER.key == "bus"
    assert BUS_SCHEDULER.name == ("bus-signal-scheduler")


def test_railway_scheduler_identity_is_stable() -> None:
    assert RAILWAY_SCHEDULER.key == "railway"
    assert RAILWAY_SCHEDULER.name == ("railway-signal-scheduler")
