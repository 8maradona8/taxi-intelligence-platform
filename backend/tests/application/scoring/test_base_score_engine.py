from datetime import UTC, datetime

import pytest

from app.application.scoring import (
    BaseScoreEngine,
    ScoreEngine,
)
from app.domain.scoring import (
    ScoreAssessment,
    ScoreContext,
    ScoreContribution,
    ScoreReason,
)


class RecordingContributor:
    def __init__(
        self,
        *,
        name: str,
        score: float,
        execution_log: list[str] | None = None,
    ) -> None:
        self._name = name
        self._score = score
        self._execution_log = execution_log

    @property
    def name(self) -> str:
        return self._name

    def evaluate(
        self,
        context: ScoreContext,
    ) -> ScoreContribution:
        if self._execution_log is not None:
            self._execution_log.append(self.name)

        return ScoreContribution(
            contributor=self.name,
            score=self._score,
            weight=1.0,
            confidence=1.0,
            reason=ScoreReason(
                code=f"{self.name}_reason",
                description=(f"{self.name} evaluated {context.subject}"),
                contribution=self._score,
            ),
        )


class RecordingAggregator:
    def __init__(self) -> None:
        self.received_contributions: tuple[ScoreContribution, ...] | None = None

    def aggregate(
        self,
        contributions: tuple[ScoreContribution, ...],
    ) -> ScoreAssessment:
        self.received_contributions = contributions

        score = sum(contribution.score for contribution in contributions) / len(
            contributions
        )

        return ScoreAssessment.create(
            score=score,
            confidence=1.0,
            contributions=contributions,
            metadata={
                "aggregator": "recording",
            },
        )


class FailingContributor:
    @property
    def name(self) -> str:
        return "failing"

    def evaluate(
        self,
        context: ScoreContext,
    ) -> ScoreContribution:
        del context

        raise RuntimeError("Contributor evaluation failed")


class MismatchedContributor:
    @property
    def name(self) -> str:
        return "registered-name"

    def evaluate(
        self,
        context: ScoreContext,
    ) -> ScoreContribution:
        del context

        return ScoreContribution(
            contributor="different-name",
            score=50.0,
            weight=1.0,
            confidence=1.0,
            reason=ScoreReason(
                code="mismatched_contributor",
                description=("Contribution uses a different contributor name"),
                contribution=50.0,
            ),
        )


def make_context() -> ScoreContext:
    return ScoreContext(
        subject="city-demand",
        observed_at=datetime(
            2026,
            7,
            23,
            8,
            0,
            tzinfo=UTC,
        ),
        attributes={
            "zone": "sofia-centre",
        },
    )


def test_base_engine_satisfies_protocol() -> None:
    engine = BaseScoreEngine(
        contributors=(
            RecordingContributor(
                name="weather",
                score=70.0,
            ),
        ),
        aggregator=RecordingAggregator(),
    )

    assert isinstance(engine, ScoreEngine)


def test_engine_requires_contributor() -> None:
    with pytest.raises(
        ValueError,
        match="At least one score contributor",
    ):
        BaseScoreEngine(
            contributors=(),
            aggregator=RecordingAggregator(),
        )


def test_engine_rejects_duplicate_names() -> None:
    with pytest.raises(
        ValueError,
        match=("Score contributor names must be unique: weather"),
    ):
        BaseScoreEngine(
            contributors=(
                RecordingContributor(
                    name="weather",
                    score=70.0,
                ),
                RecordingContributor(
                    name="weather",
                    score=80.0,
                ),
            ),
            aggregator=RecordingAggregator(),
        )


def test_engine_preserves_registration_order() -> None:
    execution_log: list[str] = []

    engine = BaseScoreEngine(
        contributors=(
            RecordingContributor(
                name="weather",
                score=70.0,
                execution_log=execution_log,
            ),
            RecordingContributor(
                name="airport",
                score=90.0,
                execution_log=execution_log,
            ),
        ),
        aggregator=RecordingAggregator(),
    )

    engine.assess(make_context())

    assert execution_log == [
        "weather",
        "airport",
    ]


def test_engine_passes_contributions_to_aggregator() -> None:
    aggregator = RecordingAggregator()

    engine = BaseScoreEngine(
        contributors=(
            RecordingContributor(
                name="weather",
                score=70.0,
            ),
            RecordingContributor(
                name="airport",
                score=90.0,
            ),
        ),
        aggregator=aggregator,
    )

    assessment = engine.assess(make_context())

    assert aggregator.received_contributions is not None
    assert assessment.score == 80.0
    assert tuple(
        contribution.contributor for contribution in aggregator.received_contributions
    ) == (
        "weather",
        "airport",
    )


def test_engine_rejects_mismatched_name() -> None:
    engine = BaseScoreEngine(
        contributors=(MismatchedContributor(),),
        aggregator=RecordingAggregator(),
    )

    with pytest.raises(
        ValueError,
        match=("expected 'registered-name', received 'different-name'"),
    ):
        engine.assess(make_context())


def test_engine_propagates_contributor_failure() -> None:
    engine = BaseScoreEngine(
        contributors=(FailingContributor(),),
        aggregator=RecordingAggregator(),
    )

    with pytest.raises(
        RuntimeError,
        match="Contributor evaluation failed",
    ):
        engine.assess(make_context())
