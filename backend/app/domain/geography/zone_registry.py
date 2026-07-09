from dataclasses import dataclass, field

from app.domain.geography.zone import Zone


@dataclass
class ZoneRegistry:
    zones: dict[str, Zone] = field(default_factory=dict)

    def register(self, zone: Zone) -> None:
        self.zones[zone.name] = zone

    def get(self, name: str) -> Zone | None:
        return self.zones.get(name)

    def all(self) -> list[Zone]:
        return list(self.zones.values())

    def count(self) -> int:
        return len(self.zones)

    def exists(self, name: str) -> bool:
        return name in self.zones