from dataclasses import dataclass
from math import isfinite

from app.domain.enums import SignalSource


@dataclass(frozen=True, slots=True)
class DemandSourceWeight:
    """Relative fusion weight assigned to one signal source."""

    source: SignalSource
    weight: float

    def __post_init__(self) -> None:
        if not isfinite(self.weight):
            raise ValueError("weight must be finite")

        if self.weight <= 0.0:
            raise ValueError("weight must be greater than 0.0")
