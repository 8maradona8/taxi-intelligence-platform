import pytest

from app.application.interfaces import SchedulerIdentity
from app.schedulers import SchedulerRegistry


class FakeStatus:
    name = "weather-signal-scheduler"
    running = True


class FakeRuntime:
    @property
    def status(self) -> FakeStatus:
        return FakeStatus()


def make_weather_identity() -> SchedulerIdentity:
    return SchedulerIdentity(
        key="weather",
        name="weather-signal-scheduler",
    )


def test_registry_registers_scheduler_metadata() -> None:
    registry = SchedulerRegistry()

    registration = registry.register(
        identity=make_weather_identity(),
        enabled=True,
    )

    assert len(registry) == 1
    assert registration.identity.key == "weather"
    assert registration.enabled is True
    assert registration.initialized is False
    assert registration.running is False


def test_registry_rejects_duplicate_key() -> None:
    registry = SchedulerRegistry()
    identity = make_weather_identity()

    registry.register(
        identity=identity,
        enabled=True,
    )

    with pytest.raises(
        ValueError,
        match="scheduler key is already registered",
    ):
        registry.register(
            identity=identity,
            enabled=True,
        )


def test_registry_resolves_normalized_key() -> None:
    registry = SchedulerRegistry()

    registry.register(
        identity=make_weather_identity(),
        enabled=True,
    )

    registration = registry.get("  WEATHER ")

    assert registration.identity.key == "weather"


def test_registry_rejects_unknown_scheduler() -> None:
    registry = SchedulerRegistry()

    with pytest.raises(
        KeyError,
        match="unknown scheduler key",
    ):
        registry.get("missing")


def test_registry_attaches_and_detaches_runtime() -> None:
    registry = SchedulerRegistry()

    registry.register(
        identity=make_weather_identity(),
        enabled=True,
    )

    attached = registry.attach_runtime(
        scheduler_key="weather",
        runtime=FakeRuntime(),
    )

    assert attached.initialized is True
    assert attached.running is True
    assert registry.get_runtime("weather") is not None

    detached = registry.detach_runtime("weather")

    assert detached.initialized is False
    assert detached.running is False
    assert registry.get_runtime("weather") is None
