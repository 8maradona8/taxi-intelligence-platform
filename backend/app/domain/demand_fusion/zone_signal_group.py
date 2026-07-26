from dataclasses import dataclass

from app.domain.demand_fusion.demand_signal_input import (
    DemandSignalInput,
)


@dataclass(frozen=True, slots=True)
class ZoneSignalGroup:
    """Immutable collection of demand signals for one zone."""

    zone_name: str
    signals: tuple[DemandSignalInput, ...]

    def __post_init__(self) -> None:
        normalized_zone_name = self.zone_name.strip()

        if not normalized_zone_name:
            raise ValueError("zone_name cannot be empty")

        if not self.signals:
            raise ValueError("signals cannot be empty")

        mismatched_zones = {
            signal.zone_name
            for signal in self.signals
            if signal.zone_name != normalized_zone_name
        }

        if mismatched_zones:
            raise ValueError("all signals must belong to the group zone")

        object.__setattr__(
            self,
            "zone_name",
            normalized_zone_name,
        )

    @property
    def signal_count(self) -> int:
        return len(self.signals)
