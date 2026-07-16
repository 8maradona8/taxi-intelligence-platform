import pytest

from app.application.interfaces import (
    AIRPORT_SCHEDULER,
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
