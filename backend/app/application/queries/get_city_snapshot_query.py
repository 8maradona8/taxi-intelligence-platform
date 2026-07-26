from dataclasses import dataclass


@dataclass(frozen=True)
class GetCitySnapshotQuery:
    city_name: str
