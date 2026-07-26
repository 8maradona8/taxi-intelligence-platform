from collections import Counter
from datetime import UTC, datetime
from math import fsum

from app.application.demand_fusion.demand_source_weight_registry import (
    DemandSourceWeightRegistry,
)
from app.domain.demand_fusion import (
    DemandSignalInput,
    DemandSourceAssessment,
    DemandSourceWeight,
)
from app.domain.enums import SignalSource


class DemandWeightNormalizer:
    """Normalize configured source weights across active signals.

    Normalization happens first at source level. When multiple active
    signals belong to the same source, that source's normalized share
    is divided equally among its signals.

    This prevents a noisy source from gaining additional influence
    solely because it emitted more signals.
    """

    def __init__(
        self,
        *,
        registry: DemandSourceWeightRegistry,
    ) -> None:
        if not registry:
            raise ValueError("Demand source weight registry cannot be empty")

        self._registry = registry

    @property
    def registry(
        self,
    ) -> DemandSourceWeightRegistry:
        return self._registry

    def normalize(
        self,
        signals: tuple[DemandSignalInput, ...],
        *,
        observed_at: datetime,
    ) -> tuple[DemandSourceAssessment, ...]:
        """Create normalized assessments for active signals."""
        normalized_observed_at = self._normalize_datetime(observed_at)

        if not signals:
            raise ValueError("At least one demand signal is required")

        active_signals = tuple(
            signal for signal in signals if signal.is_active_at(normalized_observed_at)
        )

        if not active_signals:
            raise ValueError("At least one active demand signal is required")

        active_sources = tuple(
            dict.fromkeys(signal.source for signal in active_signals)
        )

        source_weights = {
            source: self._registry.require(source) for source in active_sources
        }

        total_source_weight = fsum(
            source_weight.weight for source_weight in source_weights.values()
        )

        if total_source_weight <= 0.0:
            raise ValueError("Total active source weight must be greater than 0.0")

        signal_counts = Counter(signal.source for signal in active_signals)

        assessments = tuple(
            DemandSourceAssessment(
                signal=signal,
                source_weight=source_weights[signal.source],
                normalized_weight=self._signal_weight(
                    source=signal.source,
                    source_weights=source_weights,
                    signal_counts=signal_counts,
                    total_source_weight=(total_source_weight),
                ),
            )
            for signal in active_signals
        )

        self._validate_normalized_total(assessments)

        return assessments

    @staticmethod
    def _signal_weight(
        *,
        source: SignalSource,
        source_weights: dict[
            SignalSource,
            DemandSourceWeight,
        ],
        signal_counts: Counter[SignalSource],
        total_source_weight: float,
    ) -> float:
        source_share = source_weights[source].weight / total_source_weight
        signal_count = signal_counts[source]

        return source_share / signal_count

    @staticmethod
    def _validate_normalized_total(
        assessments: tuple[
            DemandSourceAssessment,
            ...,
        ],
    ) -> None:
        normalized_total = fsum(
            assessment.normalized_weight for assessment in assessments
        )

        if abs(normalized_total - 1.0) > 1e-9:
            raise RuntimeError("Normalized demand weights must sum to 1.0")

    @staticmethod
    def _normalize_datetime(
        value: datetime,
    ) -> datetime:
        if value.tzinfo is None:
            raise ValueError("observed_at must be timezone-aware")

        return value.astimezone(UTC)
