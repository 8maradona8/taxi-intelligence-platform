from datetime import UTC, datetime

import pytest

from app.application.scoring import (
    BaseScoreEngine,
    WeightedScoreAggregator,
)
from app.domain.scoring import (
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
        weight: float,
        confidence: float,
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
        return ScoreContribution(
            contributor=self.name,
            score=self._score,
            weight=self._weight,
            confidence=self._confidence,
            reason=ScoreReason(
                code=f"{self.name}_signal",
                description=(f"{self.name} evaluated {context.subject}"),
                contribution=self._score,
            ),
        )


def test_engine_integrates_with_weighted_aggregator() -> None:
    engine = BaseScoreEngine(
        contributors=(
            StaticContributor(
                name="weather",
                score=90.0,
                weight=0.50,
                confidence=0.20,
            ),
            StaticContributor(
                name="airport",
                score=30.0,
                weight=0.50,
                confidence=1.0,
            ),
        ),
        aggregator=WeightedScoreAggregator(),
    )

    context = ScoreContext(
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

    assessment = engine.assess(context)

    assert assessment.score == pytest.approx(40.0)
    assert assessment.confidence == pytest.approx(0.60)
    assert tuple(
        contribution.contributor for contribution in assessment.contributions
    ) == (
        "weather",
        "airport",
    )
    assert tuple(reason.code for reason in assessment.reasons) == (
        "weather_signal",
        "airport_signal",
    )
