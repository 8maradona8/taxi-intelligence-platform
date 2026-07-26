from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class BusArrival:
    origin: str
    route: str
    full_route: str
    carrier: str
    scheduled_arrival: datetime

    operating_days: tuple[str, ...] = ()
    valid_from: date | None = None
    valid_until: date | None = None
    sector: str | None = None
    source: str = "sofia_central_bus_station"

    def __post_init__(self) -> None:
        origin = self.origin.strip()
        route = self.route.strip()
        full_route = self.full_route.strip()
        carrier = self.carrier.strip()

        if not origin:
            raise ValueError("origin cannot be empty")

        if not route:
            raise ValueError("route cannot be empty")

        if not full_route:
            raise ValueError("full_route cannot be empty")

        if not carrier:
            raise ValueError("carrier cannot be empty")

        if self.scheduled_arrival.tzinfo is None:
            raise ValueError("scheduled_arrival must be timezone-aware")

        normalized_days = tuple(
            day.strip().lower() for day in self.operating_days if day.strip()
        )

        object.__setattr__(
            self,
            "origin",
            origin,
        )
        object.__setattr__(
            self,
            "route",
            route,
        )
        object.__setattr__(
            self,
            "full_route",
            full_route,
        )
        object.__setattr__(
            self,
            "carrier",
            carrier,
        )
        object.__setattr__(
            self,
            "operating_days",
            normalized_days,
        )

        if self.sector is not None:
            normalized_sector = self.sector.strip()

            object.__setattr__(
                self,
                "sector",
                normalized_sector or None,
            )
