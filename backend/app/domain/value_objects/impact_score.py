from dataclasses import dataclass


@dataclass(frozen=True)
class ImpactScore:
    value: float

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("Impact score cannot be negative")