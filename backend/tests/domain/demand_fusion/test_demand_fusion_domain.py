from datetime import UTC, datetime, timedelta

import pytest

from app.domain.demand_fusion import (
    DemandFusionAssessment,
    DemandSignalInput,
    DemandSourceAssessment,
    DemandSourceWeight,
)
from app.domain.enums import (
    PriorityLevel,
    SignalSource,
    SignalType,
)
from app.domain.events import SignalEvent
from app.domain.scoring import ScoreLevel
from app.domain.value_objects import (
    Confidence,
    ImpactScore,
)


def make_signal_input(
    *,
    source: SignalSource = SignalSource.WEATHER,
    signal_type: SignalType = (SignalType.WEATHER_CONDITION),
    zone_name: str = "Sofia Center",
    score: float = 70.0,
    confidence: float = 0.8,
    observed_at: datetime | None = None,
) -> DemandSignalInput:
    signal_observed_at = observed_at or datetime(
        2026,
        7,
        26,
        12,
        0,
        tzinfo=UTC,
    )

    return DemandSignalInput(
        source=source,
        signal_type=signal_type,
        zone_name=zone_name,
        score=score,
        confidence=confidence,
        observed_at=signal_observed_at,
        expires_at=(signal_observed_at + timedelta(minutes=30)),
    )


def make_source_assessment(
    *,
    signal: DemandSignalInput | None = None,
    weight: float = 1.0,
    normalized_weight: float = 1.0,
) -> DemandSourceAssessment:
    input_signal = signal or make_signal_input()

    return DemandSourceAssessment(
        signal=input_signal,
        source_weight=DemandSourceWeight(
            source=input_signal.source,
            weight=weight,
        ),
        normalized_weight=normalized_weight,
    )


def test_signal_input_can_be_created_from_signal_event() -> None:
    observed_at = datetime(
        2026,
        7,
        26,
        12,
        0,
        tzinfo=UTC,
    )
    event = SignalEvent(
        source=SignalSource.WEATHER,
        signal_type=SignalType.WEATHER_CONDITION,
        zone_name="Sofia Center",
        impact_score=ImpactScore(72.5),
        confidence=Confidence(0.9),
        priority=PriorityLevel.HIGH,
        observed_at=observed_at,
        ttl=timedelta(minutes=45),
        payload={
            "provider": "met-norway",
        },
    )

    result = DemandSignalInput.from_signal_event(event)

    assert result.source == SignalSource.WEATHER
    assert result.score == 72.5
    assert result.confidence == 0.9
    assert result.expires_at == (observed_at + timedelta(minutes=45))
    assert result.metadata == {
        "provider": "met-norway",
    }


def test_signal_input_reports_activity_at_moment() -> None:
    signal = make_signal_input()

    assert signal.is_active_at(signal.observed_at)
    assert signal.is_active_at(signal.expires_at - timedelta(seconds=1))
    assert not signal.is_active_at(signal.expires_at)


@pytest.mark.parametrize(
    ("score", "message"),
    [
        (-0.01, "score must be between"),
        (100.01, "score must be between"),
    ],
)
def test_signal_input_rejects_invalid_score(
    score: float,
    message: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=message,
    ):
        make_signal_input(score=score)


def test_source_weight_accepts_relative_weight() -> None:
    source_weight = DemandSourceWeight(
        source=SignalSource.AIRPORT,
        weight=3.0,
    )

    assert source_weight.weight == 3.0


@pytest.mark.parametrize(
    "weight",
    [
        0.0,
        -1.0,
    ],
)
def test_source_weight_rejects_non_positive_value(
    weight: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="weight must be greater than 0.0",
    ):
        DemandSourceWeight(
            source=SignalSource.AIRPORT,
            weight=weight,
        )


def test_source_assessment_exposes_weighted_values() -> None:
    assessment = make_source_assessment(
        signal=make_signal_input(
            score=80.0,
            confidence=0.75,
        ),
        weight=2.0,
        normalized_weight=0.4,
    )

    assert assessment.weighted_score == 32.0
    assert assessment.confidence_adjusted_weight == 0.3
    assert assessment.effective_score == 24.0


def test_source_assessment_rejects_source_mismatch() -> None:
    signal = make_signal_input(
        source=SignalSource.WEATHER,
    )

    with pytest.raises(
        ValueError,
        match="signal source must match",
    ):
        DemandSourceAssessment(
            signal=signal,
            source_weight=DemandSourceWeight(
                source=SignalSource.AIRPORT,
                weight=1.0,
            ),
            normalized_weight=1.0,
        )


def test_fusion_assessment_exposes_dominant_source() -> None:
    observed_at = datetime(
        2026,
        7,
        26,
        12,
        0,
        tzinfo=UTC,
    )

    weather = make_source_assessment(
        signal=make_signal_input(
            source=SignalSource.WEATHER,
            signal_type=(SignalType.WEATHER_CONDITION),
            score=80.0,
            confidence=0.75,
            observed_at=observed_at,
        ),
        weight=1.0,
        normalized_weight=0.4,
    )
    airport = make_source_assessment(
        signal=make_signal_input(
            source=SignalSource.AIRPORT,
            signal_type=(SignalType.AIRPORT_ACTIVITY),
            score=65.0,
            confidence=0.95,
            observed_at=observed_at,
        ),
        weight=2.0,
        normalized_weight=0.6,
    )

    result = DemandFusionAssessment.create(
        zone_name="Sofia Center",
        score=71.0,
        confidence=0.88,
        observed_at=observed_at,
        sources=(
            weather,
            airport,
        ),
    )

    assert result.score == 71.0
    assert result.level == ScoreLevel.HIGH
    assert result.source_count == 2
    assert result.active_source_types == (
        SignalSource.WEATHER,
        SignalSource.AIRPORT,
    )
    assert result.dominant_source.signal.source == SignalSource.AIRPORT
    assert result.dominant_sources(limit=1) == (airport,)


def test_fusion_assessment_rejects_mixed_zones() -> None:
    sofia_center = make_source_assessment(
        signal=make_signal_input(
            zone_name="Sofia Center",
        ),
    )
    airport = make_source_assessment(
        signal=make_signal_input(
            zone_name="Sofia Airport",
        ),
    )

    with pytest.raises(
        ValueError,
        match="must belong to the fusion zone",
    ):
        DemandFusionAssessment.create(
            zone_name="Sofia Center",
            score=50.0,
            confidence=0.8,
            observed_at=datetime(
                2026,
                7,
                26,
                12,
                0,
                tzinfo=UTC,
            ),
            sources=(
                sofia_center,
                airport,
            ),
        )


def test_fusion_assessment_requires_sources() -> None:
    with pytest.raises(
        ValueError,
        match="sources cannot be empty",
    ):
        DemandFusionAssessment.create(
            zone_name="Sofia Center",
            score=0.0,
            confidence=0.0,
            observed_at=datetime(
                2026,
                7,
                26,
                12,
                0,
                tzinfo=UTC,
            ),
            sources=(),
        )
