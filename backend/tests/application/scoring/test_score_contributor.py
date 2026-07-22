from datetime import UTC, datetime

from app.application.scoring import ScoreContributor
from app.domain.scoring import (
    ScoreContext,
    ScoreContribution,
    ScoreReason,
)


class FakeRainContributor:
    @property
    def name(self) -> str:
        return "rain"

    def evaluate(
        self,
        context: ScoreContext,
    ) -> ScoreContribution:
        precipitation = float(context.require("precipitation"))

        score = 80.0 if precipitation >= 2.0 else 20.0

        return ScoreContribution(
            contributor=self.name,
            score=score,
            weight=0.35,
            confidence=0.95,
            reason=ScoreReason(
                code="rain_detected",
                description=("Rain increases expected taxi demand"),
                contribution=score,
            ),
        )


def test_contributor_satisfies_protocol() -> None:
    contributor = FakeRainContributor()

    assert isinstance(
        contributor,
        ScoreContributor,
    )


def test_contributor_evaluates_context() -> None:
    contributor = FakeRainContributor()

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
            "precipitation": 3.5,
        },
    )

    contribution = contributor.evaluate(context)

    assert contribution.contributor == "rain"
    assert contribution.score == 80.0
    assert contribution.confidence == 0.95
