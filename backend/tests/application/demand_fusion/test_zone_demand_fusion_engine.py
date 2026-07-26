from datetime import UTC, datetime, timedelta

import pytest

from app.application.demand_fusion import (
    DemandSourceWeightRegistry,
    DemandWeightNormalizer,
    ZoneDemandFusionEngine,
)
from app.domain.demand_fusion import (
    DemandSignalInput,
    DemandSourceWeight,
    ZoneSignalGroup,
)
from app.domain.enums import (
    SignalSource,
    SignalType,
)
from app.domain.scoring import (
    ScoreAssessment,
    ScoreContribution,
    ScoreLevel,
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
    score: float,
    confidence: float,
    zone_name: str = "Sofia Center",
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


def make_normalizer() -> DemandWeightNormalizer:
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

    return DemandWeightNormalizer(
        registry=registry,
    )


def make_group(
    *signals: DemandSignalInput,
    zone_name: str = "Sofia Center",
) -> ZoneSignalGroup:
    return ZoneSignalGroup(
        zone_name=zone_name,
        signals=signals,
    )


def test_engine_fuses_multiple_sources_for_zone() -> None:
    airport = make_signal(
        source=SignalSource.AIRPORT,
        signal_type=SignalType.AIRPORT_ACTIVITY,
        score=80.0,
        confidence=0.8,
    )
    weather = make_signal(
        source=SignalSource.WEATHER,
        signal_type=SignalType.WEATHER_CONDITION,
        score=40.0,
        confidence=1.0,
    )

    result = ZoneDemandFusionEngine(
        normalizer=make_normalizer(),
    ).fuse(
        make_group(
            airport,
            weather,
        ),
        observed_at=OBSERVED_AT,
    )

    assert result.zone_name == "Sofia Center"
    assert result.score == pytest.approx(68.24)
    assert result.confidence == pytest.approx(0.85)
    assert result.level == ScoreLevel.HIGH
    assert result.observed_at == OBSERVED_AT
    assert result.sources[0].signal == airport
    assert result.sources[1].signal == weather


def test_engine_uses_confidence_adjusted_weights() -> None:
    airport = make_signal(
        source=SignalSource.AIRPORT,
        signal_type=SignalType.AIRPORT_ACTIVITY,
        score=100.0,
        confidence=0.2,
    )
    weather = make_signal(
        source=SignalSource.WEATHER,
        signal_type=SignalType.WEATHER_CONDITION,
        score=0.0,
        confidence=1.0,
    )

    result = ZoneDemandFusionEngine(
        normalizer=make_normalizer(),
    ).fuse(
        make_group(
            airport,
            weather,
        ),
        observed_at=OBSERVED_AT,
    )

    assert result.score == pytest.approx(37.5)
    assert result.confidence == pytest.approx(0.4)


def test_engine_prevents_duplicate_source_amplification() -> None:
    airport_high = make_signal(
        source=SignalSource.AIRPORT,
        signal_type=SignalType.AIRPORT_ACTIVITY,
        score=100.0,
        confidence=1.0,
    )
    airport_low = make_signal(
        source=SignalSource.AIRPORT,
        signal_type=SignalType.AIRPORT_ACTIVITY,
        score=0.0,
        confidence=1.0,
    )
    weather = make_signal(
        source=SignalSource.WEATHER,
        signal_type=SignalType.WEATHER_CONDITION,
        score=40.0,
        confidence=1.0,
    )

    result = ZoneDemandFusionEngine(
        normalizer=make_normalizer(),
    ).fuse(
        make_group(
            airport_high,
            airport_low,
            weather,
        ),
        observed_at=OBSERVED_AT,
    )

    assert result.score == pytest.approx(47.5)
    assert result.confidence == pytest.approx(1.0)

    assert tuple(
        assessment.normalized_weight for assessment in result.sources
    ) == pytest.approx(
        (
            0.375,
            0.375,
            0.25,
        )
    )


def test_engine_excludes_expired_signals() -> None:
    expired_airport = make_signal(
        source=SignalSource.AIRPORT,
        signal_type=SignalType.AIRPORT_ACTIVITY,
        score=100.0,
        confidence=1.0,
        observed_at=(OBSERVED_AT - timedelta(hours=2)),
        expires_at=(OBSERVED_AT - timedelta(hours=1)),
    )
    weather = make_signal(
        source=SignalSource.WEATHER,
        signal_type=SignalType.WEATHER_CONDITION,
        score=40.0,
        confidence=0.8,
    )

    result = ZoneDemandFusionEngine(
        normalizer=make_normalizer(),
    ).fuse(
        make_group(
            expired_airport,
            weather,
        ),
        observed_at=OBSERVED_AT,
    )

    assert result.score == pytest.approx(40.0)
    assert result.confidence == pytest.approx(0.8)
    assert len(result.sources) == 1
    assert result.sources[0].signal == weather
    assert result.metadata["input_signal_count"] == 2
    assert result.metadata["active_signal_count"] == 1


def test_engine_preserves_active_assessment_order() -> None:
    weather = make_signal(
        source=SignalSource.WEATHER,
        signal_type=SignalType.WEATHER_CONDITION,
        score=50.0,
        confidence=0.8,
    )
    airport = make_signal(
        source=SignalSource.AIRPORT,
        signal_type=SignalType.AIRPORT_ACTIVITY,
        score=80.0,
        confidence=0.9,
    )

    result = ZoneDemandFusionEngine(
        normalizer=make_normalizer(),
    ).fuse(
        make_group(
            weather,
            airport,
        ),
        observed_at=OBSERVED_AT,
    )

    assert tuple(assessment.signal for assessment in result.sources) == (
        weather,
        airport,
    )


def test_engine_exposes_fusion_metadata() -> None:
    airport = make_signal(
        source=SignalSource.AIRPORT,
        signal_type=SignalType.AIRPORT_ACTIVITY,
        score=80.0,
        confidence=0.9,
    )
    weather = make_signal(
        source=SignalSource.WEATHER,
        signal_type=SignalType.WEATHER_CONDITION,
        score=60.0,
        confidence=0.8,
    )

    result = ZoneDemandFusionEngine(
        normalizer=make_normalizer(),
    ).fuse(
        make_group(
            airport,
            weather,
        ),
        observed_at=OBSERVED_AT,
    )

    assert result.metadata["assessment_type"] == ("zone_demand_fusion")
    assert result.metadata["aggregation_method"] == (
        "confidence_adjusted_weighted_average"
    )
    assert result.metadata["active_sources"] == (
        "airport",
        "weather",
    )
    assert result.metadata["active_source_count"] == 2
    assert result.metadata["active_signal_count"] == 2
    assert result.metadata["input_signal_count"] == 2


def test_engine_rejects_when_all_active_confidence_is_zero() -> None:
    airport = make_signal(
        source=SignalSource.AIRPORT,
        signal_type=SignalType.AIRPORT_ACTIVITY,
        score=80.0,
        confidence=0.0,
    )
    weather = make_signal(
        source=SignalSource.WEATHER,
        signal_type=SignalType.WEATHER_CONDITION,
        score=60.0,
        confidence=0.0,
    )

    with pytest.raises(
        ValueError,
        match=("At least one contribution must have positive confidence"),
    ):
        ZoneDemandFusionEngine(
            normalizer=make_normalizer(),
        ).fuse(
            make_group(
                airport,
                weather,
            ),
            observed_at=OBSERVED_AT,
        )


def test_engine_rejects_naive_observed_at() -> None:
    weather = make_signal(
        source=SignalSource.WEATHER,
        signal_type=SignalType.WEATHER_CONDITION,
        score=60.0,
        confidence=0.8,
    )

    with pytest.raises(
        ValueError,
        match="observed_at must be timezone-aware",
    ):
        ZoneDemandFusionEngine(
            normalizer=make_normalizer(),
        ).fuse(
            make_group(weather),
            observed_at=datetime(
                2026,
                7,
                26,
                12,
                0,
            ),
        )


def test_engine_rejects_when_all_signals_are_expired() -> None:
    expired = make_signal(
        source=SignalSource.WEATHER,
        signal_type=SignalType.WEATHER_CONDITION,
        score=60.0,
        confidence=0.8,
        observed_at=(OBSERVED_AT - timedelta(hours=2)),
        expires_at=(OBSERVED_AT - timedelta(hours=1)),
    )

    with pytest.raises(
        ValueError,
        match="At least one active demand signal is required",
    ):
        ZoneDemandFusionEngine(
            normalizer=make_normalizer(),
        ).fuse(
            make_group(expired),
            observed_at=OBSERVED_AT,
        )


class RecordingScoreAggregator:
    def __init__(self) -> None:
        self.received: (
            tuple[
                ScoreContribution,
                ...,
            ]
            | None
        ) = None

    def aggregate(
        self,
        contributions: tuple[
            ScoreContribution,
            ...,
        ],
    ) -> ScoreAssessment:
        self.received = contributions

        return ScoreAssessment.create(
            score=55.0,
            confidence=0.75,
            contributions=contributions,
            metadata={
                "aggregation_method": "recording_test",
            },
        )


def test_engine_supports_score_aggregator_injection() -> None:
    weather = make_signal(
        source=SignalSource.WEATHER,
        signal_type=SignalType.WEATHER_CONDITION,
        score=60.0,
        confidence=0.8,
    )
    aggregator = RecordingScoreAggregator()

    result = ZoneDemandFusionEngine(
        normalizer=make_normalizer(),
        aggregator=aggregator,
    ).fuse(
        make_group(weather),
        observed_at=OBSERVED_AT,
    )

    assert aggregator.received is not None
    assert len(aggregator.received) == 1

    contribution = aggregator.received[0]

    assert contribution.contributor == ("demand:weather:weather_condition:1")
    assert contribution.score == 60.0
    assert contribution.weight == pytest.approx(1.0)
    assert contribution.confidence == pytest.approx(0.8)
    assert contribution.reason.code == "demand_weather"
    assert contribution.metadata["source"] == "weather"

    assert result.score == 55.0
    assert result.confidence == 0.75
    assert result.metadata["aggregation_method"] == ("recording_test")
