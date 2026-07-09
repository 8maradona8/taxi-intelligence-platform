from dataclasses import dataclass, field

from app.domain.geography.city import City


@dataclass
class Region:
    name: str
    cities: dict[str, City] = field(default_factory=dict)

    def add_city(self, city: City) -> None:
        self.cities[city.name] = city

    def get_city(self, name: str) -> City | None:
        return self.cities.get(name)

    def list_cities(self) -> list[City]:
        return list(self.cities.values())

    def city_count(self) -> int:
        return len(self.cities)