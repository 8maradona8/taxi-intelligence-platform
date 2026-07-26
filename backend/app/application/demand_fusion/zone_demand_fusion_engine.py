from datetime import datetime

from app.application.demand_fusion.demand_weight_normalizer import (
    DemandWeightNormalizer,
)
from app.application.scoring import (
    ScoreAggregator,
    WeightedScoreAggregator,
)
from app.domain.demand_fusion import (
    DemandFusionAssessment,
    DemandSourceAssessment,
    ZoneSignalGroup,
)
from app.domain.scoring import (
    ScoreContribution,
    ScoreReason,
)


class ZoneDemandFusionEngine:
    """Fuse active demand signals into one assessment for a zone."""

    AGGREGATION_TYPE = "zone_demand_fusion"

    def __init__(
        self,
        *,
        normalizer: DemandWeightNormalizer,
        aggregator: ScoreAggregator | None = None,
    ) -> None:
        self._normalizer = normalizer
        self._aggregator = (
            aggregator if aggregator is not None else WeightedScoreAggregator()
        )

    @property
    def normalizer(self) -> DemandWeightNormalizer:
        return self._normalizer

    @property
    def aggregator(self) -> ScoreAggregator:
        return self._aggregator

    def fuse(
        self,
        group: ZoneSignalGroup,
        *,
        observed_at: datetime,
    ) -> DemandFusionAssessment:
        """Create one confidence-adjusted assessment for a zone."""
        source_assessments = self._normalizer.normalize(
            group.signals,
            observed_at=observed_at,
        )

        contributions = tuple(
            self._to_score_contribution(
                assessment,
                position=position,
            )
            for position, assessment in enumerate(
                source_assessments,
                start=1,
            )
        )

        score_assessment = self._aggregator.aggregate(
            contributions,
        )

        active_sources = tuple(
            dict.fromkeys(
                assessment.signal.source.value for assessment in source_assessments
            )
        )

        return DemandFusionAssessment.create(
            zone_name=group.zone_name,
            score=score_assessment.score,
            confidence=score_assessment.confidence,
            observed_at=observed_at,
            sources=source_assessments,
            metadata={
                **dict(score_assessment.metadata),
                "assessment_type": self.AGGREGATION_TYPE,
                "zone_name": group.zone_name,
                "active_sources": active_sources,
                "active_source_count": len(active_sources),
                "active_signal_count": len(source_assessments),
                "input_signal_count": group.signal_count,
            },
        )

    @staticmethod
    def _to_score_contribution(
        assessment: DemandSourceAssessment,
        *,
        position: int,
    ) -> ScoreContribution:
        signal = assessment.signal

        contributor = (
            f"demand:{signal.source.value}:{signal.signal_type.value}:{position}"
        )

        return ScoreContribution(
            contributor=contributor,
            score=signal.score,
            weight=assessment.normalized_weight,
            confidence=signal.confidence,
            reason=ScoreReason(
                code=f"demand_{signal.source.value}",
                description=(
                    f"{signal.source.value} demand signal for zone {signal.zone_name}"
                ),
                contribution=assessment.effective_score,
                metadata={
                    "source": signal.source.value,
                    "signal_type": signal.signal_type.value,
                    "zone_name": signal.zone_name,
                },
            ),
            metadata={
                **dict(signal.metadata),
                "source": signal.source.value,
                "signal_type": signal.signal_type.value,
                "zone_name": signal.zone_name,
                "source_weight": assessment.source_weight.weight,
                "normalized_weight": (assessment.normalized_weight),
            },
        )
