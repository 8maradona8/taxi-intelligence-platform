from dataclasses import dataclass, field

from app.domain.geography.zone import Zone


@dataclass
class City:
    name: str
    country: str
    zones: dict[str, Zone] = field(default_factory=dict)

    def add_zone(self, zone: Zone) -> None:
        self.zones[zone.name] = zone

    def get_zone(self, name: str) -> Zone | None:
        return self.zones.get(name)

    def list_zones(self) -> list[Zone]:
        return list(self.zones.values())

    def zone_count(self) -> int:
        return len(self.zones)