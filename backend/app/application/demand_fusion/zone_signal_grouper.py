from app.domain.demand_fusion import (
    DemandSignalInput,
    ZoneSignalGroup,
)


class ZoneSignalGrouper:
    """Group demand signals by normalized zone name.

    Zone groups preserve the order in which zones first appear.
    Signals inside each group preserve their original input order.
    """

    def group(
        self,
        signals: tuple[DemandSignalInput, ...],
    ) -> tuple[ZoneSignalGroup, ...]:
        grouped_signals: dict[
            str,
            list[DemandSignalInput],
        ] = {}

        for signal in signals:
            grouped_signals.setdefault(
                signal.zone_name,
                [],
            ).append(signal)

        return tuple(
            ZoneSignalGroup(
                zone_name=zone_name,
                signals=tuple(zone_signals),
            )
            for zone_name, zone_signals in grouped_signals.items()
        )
