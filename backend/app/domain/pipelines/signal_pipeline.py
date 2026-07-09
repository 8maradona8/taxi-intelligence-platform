from collections import defaultdict

from app.domain.events import SignalEvent
from app.domain.geography import Coordinates, Zone


class SignalPipeline:
    def __init__(self) -> None:
        self.zones: dict[str, Zone] = {}

    def register_zone(self, zone: Zone) -> None:
        self.zones[zone.name] = zone

    def process(self, signals: list[SignalEvent]) -> list[Zone]:
        grouped_signals: dict[str, list[SignalEvent]] = defaultdict(list)

        for signal in signals:
            if signal.is_expired:
                continue

            grouped_signals[signal.zone_name].append(signal)

        processed_zones: list[Zone] = []

        for zone_name, zone_signals in grouped_signals.items():
            zone = self.zones.get(zone_name)

            if zone is None:
                zone = Zone(
                    name=zone_name,
                    city="Unknown",
                    country="Unknown",
                    coordinates=Coordinates(latitude=0.0, longitude=0.0),
                )

            for signal in zone_signals:
                zone.add_signal(signal)

            processed_zones.append(zone)

        return processed_zones