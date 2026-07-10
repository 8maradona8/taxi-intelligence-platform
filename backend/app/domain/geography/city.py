from dataclasses import dataclass, field

from app.domain.geography.zone import Zone
from app.domain.geography.zone_registry import ZoneRegistry


@dataclass
class City:
    name: str
    country: str
    zone_registry: ZoneRegistry = field(default_factory=ZoneRegistry)

    def add_zone(self, zone: Zone) -> None:
        self.zone_registry.register(zone)

    def get_zone(self, name: str) -> Zone | None:
        return self.zone_registry.get(name)

    def list_zones(self) -> list[Zone]:
        return self.zone_registry.all()

    def zone_count(self) -> int:
        return self.zone_registry.count()
