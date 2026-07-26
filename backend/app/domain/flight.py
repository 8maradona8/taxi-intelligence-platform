from dataclasses import dataclass
from datetime import datetime

from app.domain.flight_status import FlightStatus


@dataclass(frozen=True)
class Flight:
    flight_number: str
    origin_city: str
    origin_iata: str | None
    scheduled_arrival: datetime
    status: FlightStatus

    airline: str | None = None
    terminal: str | None = None
    estimated_arrival: datetime | None = None
    actual_arrival: datetime | None = None
    source: str = "sofia_airport_website"

    def __post_init__(self) -> None:
        flight_number = self.flight_number.strip()
        origin_city = self.origin_city.strip()

        if not flight_number:
            raise ValueError("flight_number cannot be empty")

        if not origin_city:
            raise ValueError("origin_city cannot be empty")

        if self.origin_iata is not None:
            origin_iata = self.origin_iata.strip().upper()

            if len(origin_iata) != 3:
                raise ValueError("origin_iata must contain exactly 3 characters")

            object.__setattr__(
                self,
                "origin_iata",
                origin_iata,
            )

        object.__setattr__(
            self,
            "flight_number",
            flight_number.upper(),
        )

        object.__setattr__(
            self,
            "origin_city",
            origin_city,
        )

        if self.terminal is not None:
            object.__setattr__(
                self,
                "terminal",
                self.terminal.strip(),
            )

        if self.airline is not None:
            object.__setattr__(
                self,
                "airline",
                self.airline.strip(),
            )

    @property
    def effective_arrival(self) -> datetime:
        return self.actual_arrival or self.estimated_arrival or self.scheduled_arrival

    @property
    def delay_minutes(self) -> int:
        delay = self.effective_arrival - self.scheduled_arrival

        return max(
            0,
            round(delay.total_seconds() / 60),
        )

    @property
    def is_delayed(self) -> bool:
        return self.status == FlightStatus.DELAYED or self.delay_minutes > 0

    @property
    def is_cancelled(self) -> bool:
        return self.status == FlightStatus.CANCELLED
