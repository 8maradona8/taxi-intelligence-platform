from datetime import UTC, datetime

import pytest

from app.application.scoring import (
    BaseScoreEngine,
    ScoreEngineBuilder,
    ScoreRegistry,
    WeightedScoreAggregator,
)
from app.domain.scoring import (
    ScoreAssessment,
    ScoreContext,
    ScoreContribution,
    ScoreReason,
)


class StaticContributor:
    def __init__(
        self,
        *,
        name: str,
        score: float,
        weight: float = 1.0,
        confidence: float = 1.0,
    ) -> None:
        self._name = name
        self._score = score
        self._weight = weight
        self._confidence = confidence

    @property
    def name(self) -> str:
        return self._name

    def evaluate(
        self,
        context: ScoreContext,
    ) -> ScoreContribution:
        del context

        return ScoreContribution(
            contributor=self.name,
            score=self._score,
            weight=self._weight,
            confidence=self._confidence,
            reason=ScoreReason(
                code=f"{self.name}_reason",
                description=(f"{self.name} scoring contribution"),
                contribution=self._score,
            ),
        )


class FixedAggregator:
    def aggregate(
        self,
        contributions: tuple[ScoreContribution, ...],
    ) -> ScoreAssessment:
        return ScoreAssessment.create(
            score=25.0,
            confidence=0.50,
            contributions=contributions,
            metadata={
                "aggregator": "fixed",
            },
        )


def make_context() -> ScoreContext:
    return ScoreContext(
        subject="city-demand",
        observed_at=datetime(
            2026,
            7,
            23,
            12,
            0,
            tzinfo=UTC,
        ),
        attributes={
            "zone": "sofia-centre",
        },
    )


def test_builder_uses_empty_registry_by_default() -> None:
    builder = ScoreEngineBuilder()

    assert isinstance(
        builder.registry,
        ScoreRegistry,
    )
    assert not builder.registry


def test_builder_uses_weighted_aggregator_by_default() -> None:
    builder = ScoreEngineBuilder()

    assert isinstance(
        builder.aggregator,
        WeightedScoreAggregator,
    )


def test_add_returns_same_builder() -> None:
    builder = ScoreEngineBuilder()

    result = builder.add(
        StaticContributor(
            name="weather",
            score=70.0,
        )
    )

    assert result is builder
    assert builder.registry.names == ("weather",)


def test_add_many_preserves_order() -> None:
    builder = ScoreEngineBuilder()

    result = builder.add_many(
        (
            StaticContributor(
                name="weather",
                score=70.0,
            ),
            StaticContributor(
                name="airport",
                score=90.0,
            ),
        )
    )

    assert result is builder
    assert builder.registry.names == (
        "weather",
        "airport",
    )


def test_builder_accepts_existing_registry() -> None:
    weather = StaticContributor(
        name="weather",
        score=70.0,
    )

    builder = ScoreEngineBuilder(registry=ScoreRegistry((weather,)))

    assert builder.registry.contributors == (weather,)


def test_builder_accepts_custom_aggregator() -> None:
    aggregator = FixedAggregator()

    builder = ScoreEngineBuilder(aggregator=aggregator)

    assert builder.aggregator is aggregator


def test_with_aggregator_replaces_aggregator() -> None:
    builder = ScoreEngineBuilder()
    aggregator = FixedAggregator()

    result = builder.with_aggregator(aggregator)

    assert result is builder
    assert builder.aggregator is aggregator


def test_build_requires_registered_contributor() -> None:
    builder = ScoreEngineBuilder()

    with pytest.raises(
        ValueError,
        match="At least one score contributor",
    ):
        builder.build()


def test_build_returns_base_score_engine() -> None:
    contributor = StaticContributor(
        name="weather",
        score=70.0,
    )

    engine = ScoreEngineBuilder().add(contributor).build()

    assert isinstance(engine, BaseScoreEngine)
    assert engine.contributors == (contributor,)


def test_built_engine_uses_default_aggregator() -> None:
    engine = (
        ScoreEngineBuilder()
        .add(
            StaticContributor(
                name="weather",
                score=70.0,
            )
        )
        .build()
    )

    assert isinstance(
        engine.aggregator,
        WeightedScoreAggregator,
    )

    assessment = engine.assess(make_context())

    assert assessment.score == 70.0
    assert assessment.confidence == 1.0


def test_built_engine_uses_custom_aggregator() -> None:
    engine = (
        ScoreEngineBuilder(aggregator=FixedAggregator())
        .add(
            StaticContributor(
                name="weather",
                score=70.0,
            )
        )
        .build()
    )

    assessment = engine.assess(make_context())

    assert assessment.score == 25.0
    assert assessment.confidence == 0.50
    assert assessment.metadata == {
        "aggregator": "fixed",
    }


def test_builder_rejects_duplicate_contributors() -> None:
    builder = ScoreEngineBuilder()

    builder.add(
        StaticContributor(
            name="weather",
            score=70.0,
        )
    )

    with pytest.raises(
        ValueError,
        match=("Score contributor names must be unique: weather"),
    ):
        builder.add(
            StaticContributor(
                name="weather",
                score=90.0,
            )
        )


def test_builder_chain_creates_working_engine() -> None:
    engine = (
        ScoreEngineBuilder()
        .add(
            StaticContributor(
                name="weather",
                score=90.0,
                weight=0.50,
                confidence=0.20,
            )
        )
        .add(
            StaticContributor(
                name="airport",
                score=30.0,
                weight=0.50,
                confidence=1.0,
            )
        )
        .build()
    )

    assessment = engine.assess(make_context())

    assert assessment.score == pytest.approx(40.0)
    assert assessment.confidence == pytest.approx(0.60)
    assert tuple(
        contribution.contributor for contribution in assessment.contributions
    ) == (
        "weather",
        "airport",
    )
