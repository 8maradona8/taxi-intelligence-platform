from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from math import isfinite
from typing import Any

from app.domain.demand_fusion.demand_source_assessment import (
    DemandSourceAssessment,
)
from app.domain.enums import SignalSource
from app.domain.scoring import ScoreLevel


@dataclass(frozen=True, slots=True)
class DemandFusionAssessment:
    """Aggregated multi-source demand assessment for one zone."""

    zone_name: str
    score: float
    confidence: float
    level: ScoreLevel
    observed_at: datetime
    sources: tuple[DemandSourceAssessment, ...]
    metadata: Mapping[str, Any] = field(
        default_factory=dict,
    )

    def __post_init__(self) -> None:
        normalized_zone_name = self.zone_name.strip()

        if not normalized_zone_name:
            raise ValueError("zone_name cannot be empty")

        if not isfinite(self.score):
            raise ValueError("score must be finite")

        if not 0.0 <= self.score <= 100.0:
            raise ValueError("score must be between 0.0 and 100.0")

        if not isfinite(self.confidence):
            raise ValueError("confidence must be finite")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

        expected_level = ScoreLevel.from_score(self.score)

        if self.level != expected_level:
            raise ValueError("level does not match the supplied score")

        if self.observed_at.tzinfo is None:
            raise ValueError("observed_at must be timezone-aware")

        if not self.sources:
            raise ValueError("sources cannot be empty")

        mismatched_zones = {
            source.signal.zone_name
            for source in self.sources
            if source.signal.zone_name != normalized_zone_name
        }

        if mismatched_zones:
            raise ValueError("all source assessments must belong to the fusion zone")

        object.__setattr__(
            self,
            "zone_name",
            normalized_zone_name,
        )
        object.__setattr__(
            self,
            "observed_at",
            self.observed_at.astimezone(UTC),
        )

    @classmethod
    def create(
        cls,
        *,
        zone_name: str,
        score: float,
        confidence: float,
        observed_at: datetime,
        sources: tuple[
            DemandSourceAssessment,
            ...,
        ],
        metadata: Mapping[str, Any] | None = None,
    ) -> "DemandFusionAssessment":
        normalized_score = round(
            min(100.0, max(0.0, score)),
            2,
        )
        normalized_confidence = round(
            min(1.0, max(0.0, confidence)),
            4,
        )

        return cls(
            zone_name=zone_name,
            score=normalized_score,
            confidence=normalized_confidence,
            level=ScoreLevel.from_score(normalized_score),
            observed_at=observed_at,
            sources=sources,
            metadata=metadata or {},
        )

    @property
    def source_count(self) -> int:
        return len(self.sources)

    @property
    def active_source_types(
        self,
    ) -> tuple[SignalSource, ...]:
        return tuple(dict.fromkeys(source.signal.source for source in self.sources))

    @property
    def dominant_source(
        self,
    ) -> DemandSourceAssessment:
        """Return the strongest effective contribution."""
        return max(
            self.sources,
            key=lambda source: (
                source.effective_score,
                source.weighted_score,
            ),
        )

    def dominant_sources(
        self,
        *,
        limit: int = 3,
    ) -> tuple[DemandSourceAssessment, ...]:
        if limit <= 0:
            raise ValueError("limit must be greater than 0")

        ordered_sources = sorted(
            self.sources,
            key=lambda source: (
                source.effective_score,
                source.weighted_score,
            ),
            reverse=True,
        )

        return tuple(ordered_sources[:limit])
