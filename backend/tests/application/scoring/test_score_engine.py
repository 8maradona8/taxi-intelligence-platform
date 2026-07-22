from datetime import UTC, datetime

from app.application.scoring import ScoreEngine
from app.domain.scoring import (
    ScoreAssessment,
    ScoreContext,
)


class FakeScoreEngine:
    def assess(
        self,
        context: ScoreContext,
    ) -> ScoreAssessment:
        base_score = float(context.require("base_score"))

        return ScoreAssessment.create(
            score=base_score,
            confidence=0.90,
            metadata={
                "subject": context.subject,
            },
        )


def test_engine_satisfies_protocol() -> None:
    engine = FakeScoreEngine()

    assert isinstance(
        engine,
        ScoreEngine,
    )


def test_engine_returns_assessment() -> None:
    engine = FakeScoreEngine()

    context = ScoreContext(
        subject="weather",
        observed_at=datetime(
            2026,
            7,
            22,
            12,
            0,
            tzinfo=UTC,
        ),
        attributes={
            "base_score": 75.0,
        },
    )

    assessment = engine.assess(context)

    assert assessment.score == 75.0
    assert assessment.confidence == 0.90
    assert assessment.metadata["subject"] == "weather"
