from dataclasses import dataclass
from datetime import datetime

from app.domain.train_status import TrainStatus


@dataclass(frozen=True)
class TrainArrival:
    train_number: str
    train_type_code: str
    train_type_name: str
    origin_station: str
    scheduled_arrival: datetime
    status: TrainStatus

    expected_arrival: datetime | None = None
    delay_minutes: int = 0
    platform: str | None = None
    source: str = "bdz_live_board"

    def __post_init__(self) -> None:
        train_number = self.train_number.strip()
        train_type_code = self.train_type_code.strip().upper()
        train_type_name = self.train_type_name.strip()
        origin_station = self.origin_station.strip()

        if not train_number:
            raise ValueError("train_number cannot be empty")

        if not train_type_code:
            raise ValueError("train_type_code cannot be empty")

        if not train_type_name:
            raise ValueError("train_type_name cannot be empty")

        if not origin_station:
            raise ValueError("origin_station cannot be empty")

        object.__setattr__(
            self,
            "train_number",
            train_number,
        )
        object.__setattr__(
            self,
            "train_type_code",
            train_type_code,
        )
        object.__setattr__(
            self,
            "train_type_name",
            train_type_name,
        )
        object.__setattr__(
            self,
            "origin_station",
            origin_station,
        )

        if self.platform is not None:
            normalized_platform = self.platform.strip()

            object.__setattr__(
                self,
                "platform",
                normalized_platform or None,
            )

    @property
    def effective_arrival(self) -> datetime:
        return self.expected_arrival or self.scheduled_arrival

    @property
    def is_delayed(self) -> bool:
        return self.status == TrainStatus.DELAYED or self.delay_minutes > 0

    @property
    def is_early(self) -> bool:
        return self.status == TrainStatus.EARLY or self.delay_minutes < 0

    @property
    def is_cancelled(self) -> bool:
        return self.status == TrainStatus.CANCELLED
