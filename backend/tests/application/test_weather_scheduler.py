from datetime import timedelta

import pytest

from app.domain.enums import (
    PriorityLevel,
    SignalSource,
    SignalType,
)
from app.domain.events import SignalEvent
from app.domain.value_objects import (
    Confidence,
    ImpactScore,
)
from app.schedulers import WeatherScheduler


def make_signal() -> SignalEvent:
    return SignalEvent(
        source=SignalSource.WEATHER,
        signal_type=SignalType.WEATHER_CONDITION,
        zone_name="Sofia",
        impact_score=ImpactScore(0.0),
        confidence=Confidence(0.95),
        priority=PriorityLevel.LOW,
        ttl=timedelta(minutes=30),
        payload={
            "provider": "met-norway",
            "arrivals": 0,
            "forecast_count": 6,
        },
    )


@pytest.mark.anyio
async def test_weather_scheduler_executes_job() -> None:
    calls = 0

    async def fake_job() -> SignalEvent:
        nonlocal calls
        calls += 1

        return make_signal()

    scheduler = WeatherScheduler(
        job=fake_job,
        interval_seconds=900,
        run_on_startup=False,
    )

    signal = await scheduler.run_once()

    assert signal is not None
    assert calls == 1
    assert scheduler.status.name == ("weather-signal-scheduler")
    assert scheduler.status.successes_total == 1
    assert scheduler.status.last_arrivals == 0
    assert scheduler.status.last_impact_score == 0.0


@pytest.mark.anyio
async def test_weather_scheduler_tracks_failure() -> None:
    async def failing_job() -> SignalEvent:
        raise RuntimeError("MET Norway source unavailable")

    scheduler = WeatherScheduler(
        job=failing_job,
        interval_seconds=900,
        run_on_startup=False,
    )

    with pytest.raises(
        RuntimeError,
        match="MET Norway source unavailable",
    ):
        await scheduler.run_once()

    assert scheduler.status.failures_total == 1
    assert scheduler.status.last_error == (
        "RuntimeError: MET Norway source unavailable"
    )
