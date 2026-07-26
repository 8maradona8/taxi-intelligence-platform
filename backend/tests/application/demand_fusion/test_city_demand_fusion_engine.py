from datetime import UTC, datetime, timedelta

import pytest

from app.application.demand_fusion import (
    CityDemandFusionEngine,
    DemandSourceWeightRegistry,
    DemandWeightNormalizer,
    ZoneDemandFusionEngine,
    ZoneSignalGrouper,
)
from app.domain.demand_fusion import (
    DemandSignalInput,
    DemandSourceWeight,
)
from app.domain.enums import (
    SignalSource,
    SignalType,
)


OBSERVED_AT = datetime(
    2026,
    7,
    26,
    12,
    0,
    tzinfo=UTC,
)


def make_signal(
    *,
    zone_name: str,
    source: SignalSource,
    signal_type: SignalType,
    score: float,
    confidence: float,
    observed_at: datetime = OBSERVED_AT,
    expires_at: datetime | None = None,
) -> DemandSignalInput:
    return DemandSignalInput(
        source=source,
        signal_type=signal_type,
        zone_name=zone_name,
        score=score,
        confidence=confidence,
        observed_at=observed_at,
        expires_at=(expires_at or observed_at + timedelta(minutes=60)),
    )


def make_engine() -> CityDemandFusionEngine:
    registry = DemandSourceWeightRegistry(
        (
            DemandSourceWeight(
                source=SignalSource.AIRPORT,
                weight=3.0,
            ),
            DemandSourceWeight(
                source=SignalSource.EVENTS,
                weight=2.0,
            ),
            DemandSourceWeight(
                source=SignalSource.TRANSPORT,
                weight=2.0,
            ),
            DemandSourceWeight(
                source=SignalSource.WEATHER,
                weight=1.0,
            ),
            DemandSourceWeight(
                source=SignalSource.TRAFFIC,
                weight=1.5,
            ),
        )
    )
    normalizer = DemandWeightNormalizer(
        registry=registry,
    )
    zone_engine = ZoneDemandFusionEngine(
        normalizer=normalizer,
    )

    return CityDemandFusionEngine(
        grouper=ZoneSignalGrouper(),
        zone_engine=zone_engine,
    )


def test_engine_fuses_and_ranks_city_zones() -> None:
    center_weather = make_signal(
        zone_name="Sofia Center",
        source=SignalSource.WEATHER,
        signal_type=SignalType.WEATHER_CONDITION,
        score=60.0,
        confidence=0.8,
    )
    airport_activity = make_signal(
        zone_name="Sofia Airport",
        source=SignalSource.AIRPORT,
        signal_type=SignalType.AIRPORT_ACTIVITY,
        score=90.0,
        confidence=0.9,
    )
    center_event = make_signal(
        zone_name="Sofia Center",
        source=SignalSource.EVENTS,
        signal_type=SignalType.EVENT_ACTIVITY,
        score=80.0,
        confidence=0.9,
    )

    results = make_engine().fuse(
        (
            center_weather,
            airport_activity,
            center_event,
        ),
        observed_at=OBSERVED_AT,
    )

    assert isinstance(results, tuple)
    assert tuple(assessment.zone_name for assessment in results) == (
        "Sofia Airport",
        "Sofia Center",
    )

    assert results[0].score == pytest.approx(90.0)
    assert results[1].score == pytest.approx(73.85)
    assert results[1].source_count == 2


def test_engine_filters_expired_signals_before_grouping() -> None:
    expired_airport = make_signal(
        zone_name="Sofia Airport",
        source=SignalSource.AIRPORT,
        signal_type=SignalType.AIRPORT_ACTIVITY,
        score=100.0,
        confidence=1.0,
        observed_at=(OBSERVED_AT - timedelta(hours=2)),
        expires_at=(OBSERVED_AT - timedelta(hours=1)),
    )
    center_weather = make_signal(
        zone_name="Sofia Center",
        source=SignalSource.WEATHER,
        signal_type=SignalType.WEATHER_CONDITION,
        score=50.0,
        confidence=0.8,
    )

    results = make_engine().fuse(
        (
            expired_airport,
            center_weather,
        ),
        observed_at=OBSERVED_AT,
    )

    assert len(results) == 1
    assert results[0].zone_name == "Sofia Center"
    assert results[0].sources[0].signal == center_weather


def test_engine_returns_empty_tuple_for_empty_input() -> None:
    results = make_engine().fuse(
        (),
        observed_at=OBSERVED_AT,
    )

    assert results == ()
    assert isinstance(results, tuple)


def test_engine_returns_empty_tuple_when_all_signals_expired() -> None:
    expired = make_signal(
        zone_name="Sofia Airport",
        source=SignalSource.AIRPORT,
        signal_type=SignalType.AIRPORT_ACTIVITY,
        score=100.0,
        confidence=1.0,
        observed_at=(OBSERVED_AT - timedelta(hours=2)),
        expires_at=(OBSERVED_AT - timedelta(hours=1)),
    )

    results = make_engine().fuse(
        (expired,),
        observed_at=OBSERVED_AT,
    )

    assert results == ()


def test_engine_uses_confidence_as_secondary_ranking() -> None:
    airport = make_signal(
        zone_name="Sofia Airport",
        source=SignalSource.AIRPORT,
        signal_type=SignalType.AIRPORT_ACTIVITY,
        score=70.0,
        confidence=0.7,
    )
    center = make_signal(
        zone_name="Sofia Center",
        source=SignalSource.WEATHER,
        signal_type=SignalType.WEATHER_CONDITION,
        score=70.0,
        confidence=0.9,
    )

    results = make_engine().fuse(
        (
            airport,
            center,
        ),
        observed_at=OBSERVED_AT,
    )

    assert tuple(assessment.zone_name for assessment in results) == (
        "Sofia Center",
        "Sofia Airport",
    )


def test_engine_uses_zone_name_as_final_tie_breaker() -> None:
    lozenets = make_signal(
        zone_name="Lozenets",
        source=SignalSource.WEATHER,
        signal_type=SignalType.WEATHER_CONDITION,
        score=70.0,
        confidence=0.8,
    )
    airport = make_signal(
        zone_name="Airport",
        source=SignalSource.WEATHER,
        signal_type=SignalType.WEATHER_CONDITION,
        score=70.0,
        confidence=0.8,
    )

    results = make_engine().fuse(
        (
            lozenets,
            airport,
        ),
        observed_at=OBSERVED_AT,
    )

    assert tuple(assessment.zone_name for assessment in results) == (
        "Airport",
        "Lozenets",
    )


def test_engine_output_is_independent_of_input_zone_order() -> None:
    airport = make_signal(
        zone_name="Sofia Airport",
        source=SignalSource.AIRPORT,
        signal_type=SignalType.AIRPORT_ACTIVITY,
        score=85.0,
        confidence=0.9,
    )
    center = make_signal(
        zone_name="Sofia Center",
        source=SignalSource.EVENTS,
        signal_type=SignalType.EVENT_ACTIVITY,
        score=65.0,
        confidence=0.8,
    )

    engine = make_engine()

    first = engine.fuse(
        (
            center,
            airport,
        ),
        observed_at=OBSERVED_AT,
    )
    second = engine.fuse(
        (
            airport,
            center,
        ),
        observed_at=OBSERVED_AT,
    )

    assert tuple(assessment.zone_name for assessment in first) == tuple(
        assessment.zone_name for assessment in second
    )

    assert tuple(assessment.score for assessment in first) == tuple(
        assessment.score for assessment in second
    )


def test_engine_normalizes_observed_at_to_utc() -> None:
    eastern_europe_time = datetime.fromisoformat("2026-07-26T15:00:00+03:00")
    signal = make_signal(
        zone_name="Sofia Center",
        source=SignalSource.WEATHER,
        signal_type=SignalType.WEATHER_CONDITION,
        score=70.0,
        confidence=0.8,
    )

    results = make_engine().fuse(
        (signal,),
        observed_at=eastern_europe_time,
    )

    assert results[0].observed_at == OBSERVED_AT
    assert results[0].observed_at.tzinfo == UTC


def test_engine_rejects_naive_observed_at_for_empty_input() -> None:
    with pytest.raises(
        ValueError,
        match="observed_at must be timezone-aware",
    ):
        make_engine().fuse(
            (),
            observed_at=datetime(
                2026,
                7,
                26,
                12,
                0,
            ),
        )


def test_engine_exposes_injected_dependencies() -> None:
    grouper = ZoneSignalGrouper()
    registry = DemandSourceWeightRegistry(
        (
            DemandSourceWeight(
                source=SignalSource.WEATHER,
                weight=1.0,
            ),
        )
    )
    zone_engine = ZoneDemandFusionEngine(
        normalizer=DemandWeightNormalizer(
            registry=registry,
        ),
    )

    engine = CityDemandFusionEngine(
        grouper=grouper,
        zone_engine=zone_engine,
    )

    assert engine.grouper is grouper
    assert engine.zone_engine is zone_engine
