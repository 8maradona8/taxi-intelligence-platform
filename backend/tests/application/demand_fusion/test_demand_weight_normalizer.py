from datetime import UTC, datetime, timedelta
from math import fsum

import pytest

from app.application.demand_fusion import (
    DemandSourceWeightRegistry,
    DemandWeightNormalizer,
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
    source: SignalSource,
    signal_type: SignalType,
    score: float = 70.0,
    confidence: float = 0.8,
    observed_at: datetime = OBSERVED_AT,
    expires_at: datetime | None = None,
) -> DemandSignalInput:
    return DemandSignalInput(
        source=source,
        signal_type=signal_type,
        zone_name="Sofia Center",
        score=score,
        confidence=confidence,
        observed_at=observed_at,
        expires_at=(expires_at or observed_at + timedelta(minutes=60)),
    )


def make_registry() -> DemandSourceWeightRegistry:
    return DemandSourceWeightRegistry(
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


def test_normalizer_normalizes_active_sources() -> None:
    normalizer = DemandWeightNormalizer(registry=make_registry())
    airport = make_signal(
        source=SignalSource.AIRPORT,
        signal_type=SignalType.AIRPORT_ACTIVITY,
    )
    weather = make_signal(
        source=SignalSource.WEATHER,
        signal_type=SignalType.WEATHER_CONDITION,
    )

    assessments = normalizer.normalize(
        (
            airport,
            weather,
        ),
        observed_at=OBSERVED_AT,
    )

    assert len(assessments) == 2
    assert assessments[0].normalized_weight == pytest.approx(0.75)
    assert assessments[1].normalized_weight == pytest.approx(0.25)
    assert fsum(
        assessment.normalized_weight for assessment in assessments
    ) == pytest.approx(1.0)


def test_multiple_signals_share_their_source_weight() -> None:
    normalizer = DemandWeightNormalizer(registry=make_registry())
    airport_one = make_signal(
        source=SignalSource.AIRPORT,
        signal_type=SignalType.AIRPORT_ACTIVITY,
        score=80.0,
    )
    airport_two = make_signal(
        source=SignalSource.AIRPORT,
        signal_type=SignalType.AIRPORT_ACTIVITY,
        score=60.0,
    )
    weather = make_signal(
        source=SignalSource.WEATHER,
        signal_type=SignalType.WEATHER_CONDITION,
    )

    assessments = normalizer.normalize(
        (
            airport_one,
            airport_two,
            weather,
        ),
        observed_at=OBSERVED_AT,
    )

    assert assessments[0].normalized_weight == pytest.approx(0.375)
    assert assessments[1].normalized_weight == pytest.approx(0.375)
    assert assessments[2].normalized_weight == pytest.approx(0.25)


def test_expired_signals_are_excluded() -> None:
    normalizer = DemandWeightNormalizer(registry=make_registry())
    expired_airport = make_signal(
        source=SignalSource.AIRPORT,
        signal_type=SignalType.AIRPORT_ACTIVITY,
        observed_at=OBSERVED_AT - timedelta(hours=2),
        expires_at=OBSERVED_AT - timedelta(hours=1),
    )
    weather = make_signal(
        source=SignalSource.WEATHER,
        signal_type=SignalType.WEATHER_CONDITION,
    )

    assessments = normalizer.normalize(
        (
            expired_airport,
            weather,
        ),
        observed_at=OBSERVED_AT,
    )

    assert len(assessments) == 1
    assert assessments[0].signal.source == SignalSource.WEATHER
    assert assessments[0].normalized_weight == pytest.approx(1.0)


def test_normalizer_preserves_active_signal_order() -> None:
    normalizer = DemandWeightNormalizer(registry=make_registry())
    weather = make_signal(
        source=SignalSource.WEATHER,
        signal_type=SignalType.WEATHER_CONDITION,
    )
    airport = make_signal(
        source=SignalSource.AIRPORT,
        signal_type=SignalType.AIRPORT_ACTIVITY,
    )

    assessments = normalizer.normalize(
        (
            weather,
            airport,
        ),
        observed_at=OBSERVED_AT,
    )

    assert tuple(assessment.signal for assessment in assessments) == (
        weather,
        airport,
    )


def test_normalizer_requires_registered_active_source() -> None:
    registry = DemandSourceWeightRegistry(
        (
            DemandSourceWeight(
                source=SignalSource.WEATHER,
                weight=1.0,
            ),
        )
    )
    normalizer = DemandWeightNormalizer(registry=registry)
    airport = make_signal(
        source=SignalSource.AIRPORT,
        signal_type=SignalType.AIRPORT_ACTIVITY,
    )

    with pytest.raises(
        KeyError,
        match=("Demand source weight is not registered: airport"),
    ):
        normalizer.normalize(
            (airport,),
            observed_at=OBSERVED_AT,
        )


def test_normalizer_rejects_empty_signal_collection() -> None:
    normalizer = DemandWeightNormalizer(registry=make_registry())

    with pytest.raises(
        ValueError,
        match="At least one demand signal is required",
    ):
        normalizer.normalize(
            (),
            observed_at=OBSERVED_AT,
        )


def test_normalizer_rejects_when_all_signals_expired() -> None:
    normalizer = DemandWeightNormalizer(registry=make_registry())
    expired = make_signal(
        source=SignalSource.WEATHER,
        signal_type=SignalType.WEATHER_CONDITION,
        observed_at=OBSERVED_AT - timedelta(hours=2),
        expires_at=OBSERVED_AT - timedelta(hours=1),
    )

    with pytest.raises(
        ValueError,
        match=("At least one active demand signal is required"),
    ):
        normalizer.normalize(
            (expired,),
            observed_at=OBSERVED_AT,
        )


def test_normalizer_requires_aware_observed_at() -> None:
    normalizer = DemandWeightNormalizer(registry=make_registry())
    weather = make_signal(
        source=SignalSource.WEATHER,
        signal_type=SignalType.WEATHER_CONDITION,
    )

    with pytest.raises(
        ValueError,
        match="observed_at must be timezone-aware",
    ):
        normalizer.normalize(
            (weather,),
            observed_at=datetime(
                2026,
                7,
                26,
                12,
                0,
            ),
        )


def test_normalizer_rejects_empty_registry() -> None:
    with pytest.raises(
        ValueError,
        match=("Demand source weight registry cannot be empty"),
    ):
        DemandWeightNormalizer(registry=DemandSourceWeightRegistry())
