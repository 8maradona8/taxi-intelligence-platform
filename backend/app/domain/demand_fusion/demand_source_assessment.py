from dataclasses import dataclass
from math import isfinite

from app.domain.demand_fusion.demand_signal_input import (
    DemandSignalInput,
)
from app.domain.demand_fusion.demand_source_weight import (
    DemandSourceWeight,
)


@dataclass(frozen=True, slots=True)
class DemandSourceAssessment:
    """Weighted contribution of one input to a fusion result."""

    signal: DemandSignalInput
    source_weight: DemandSourceWeight
    normalized_weight: float

    def __post_init__(self) -> None:
        if self.signal.source != self.source_weight.source:
            raise ValueError("signal source must match source weight")

        if not isfinite(self.normalized_weight):
            raise ValueError("normalized_weight must be finite")

        if not 0.0 < self.normalized_weight <= 1.0:
            raise ValueError(
                "normalized_weight must be greater than 0.0 and at most 1.0"
            )

    @property
    def weighted_score(self) -> float:
        return round(
            self.signal.score * self.normalized_weight,
            4,
        )

    @property
    def confidence_adjusted_weight(self) -> float:
        return round(
            self.normalized_weight * self.signal.confidence,
            4,
        )

    @property
    def effective_score(self) -> float:
        return round(
            self.signal.score * self.confidence_adjusted_weight,
            4,
        )
