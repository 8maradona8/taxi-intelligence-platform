from collections.abc import Mapping
from dataclasses import dataclass, field
from math import isfinite
from typing import Any


@dataclass(frozen=True)
class ScoreReason:
    code: str
    description: str
    contribution: float = 0.0
    metadata: Mapping[str, Any] = field(
        default_factory=dict,
    )

    def __post_init__(self) -> None:
        normalized_code = self.code.strip()
        normalized_description = self.description.strip()

        if not normalized_code:
            raise ValueError("code cannot be empty")

        if not normalized_description:
            raise ValueError("description cannot be empty")

        if not isfinite(self.contribution):
            raise ValueError("contribution must be finite")

        if not -100.0 <= self.contribution <= 100.0:
            raise ValueError("contribution must be between -100.0 and 100.0")

        object.__setattr__(
            self,
            "code",
            normalized_code,
        )
        object.__setattr__(
            self,
            "description",
            normalized_description,
        )
