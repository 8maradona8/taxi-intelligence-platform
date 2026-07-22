from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, TypeVar


ContextValue = TypeVar("ContextValue")


@dataclass(frozen=True)
class ScoreContext:
    subject: str
    observed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    attributes: Mapping[str, Any] = field(
        default_factory=dict,
    )
    metadata: Mapping[str, Any] = field(
        default_factory=dict,
    )

    def __post_init__(self) -> None:
        normalized_subject = self.subject.strip()

        if not normalized_subject:
            raise ValueError("subject cannot be empty")

        if self.observed_at.tzinfo is None:
            raise ValueError("observed_at must be timezone-aware")

        object.__setattr__(
            self,
            "subject",
            normalized_subject,
        )
        object.__setattr__(
            self,
            "observed_at",
            self.observed_at.astimezone(UTC),
        )

    def get(
        self,
        key: str,
        default: ContextValue | None = None,
    ) -> Any | ContextValue | None:
        return self.attributes.get(key, default)

    def require(self, key: str) -> Any:
        if key not in self.attributes:
            raise KeyError(f"Required scoring attribute is missing: {key}")

        return self.attributes[key]
