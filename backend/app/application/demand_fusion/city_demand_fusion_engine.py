from datetime import UTC, datetime

from app.application.demand_fusion.zone_demand_fusion_engine import (
    ZoneDemandFusionEngine,
)
from app.application.demand_fusion.zone_signal_grouper import (
    ZoneSignalGrouper,
)
from app.domain.demand_fusion import (
    DemandFusionAssessment,
    DemandSignalInput,
)


class CityDemandFusionEngine:
    """Fuse and rank active demand signals across city zones."""

    def __init__(
        self,
        *,
        grouper: ZoneSignalGrouper,
        zone_engine: ZoneDemandFusionEngine,
    ) -> None:
        self._grouper = grouper
        self._zone_engine = zone_engine

    @property
    def grouper(self) -> ZoneSignalGrouper:
        return self._grouper

    @property
    def zone_engine(self) -> ZoneDemandFusionEngine:
        return self._zone_engine

    def fuse(
        self,
        signals: tuple[DemandSignalInput, ...],
        *,
        observed_at: datetime,
    ) -> tuple[DemandFusionAssessment, ...]:
        """Return active zone assessments ordered by opportunity."""
        normalized_observed_at = self._normalize_datetime(
            observed_at,
        )

        active_signals = tuple(
            signal for signal in signals if signal.is_active_at(normalized_observed_at)
        )

        if not active_signals:
            return ()

        groups = self._grouper.group(active_signals)

        assessments = tuple(
            self._zone_engine.fuse(
                group,
                observed_at=normalized_observed_at,
            )
            for group in groups
        )

        return tuple(
            sorted(
                assessments,
                key=self._ranking_key,
            )
        )

    @staticmethod
    def _ranking_key(
        assessment: DemandFusionAssessment,
    ) -> tuple[
        float,
        float,
        str,
        str,
    ]:
        return (
            -assessment.score,
            -assessment.confidence,
            assessment.zone_name.casefold(),
            assessment.zone_name,
        )

    @staticmethod
    def _normalize_datetime(
        value: datetime,
    ) -> datetime:
        if value.tzinfo is None:
            raise ValueError("observed_at must be timezone-aware")

        return value.astimezone(UTC)
