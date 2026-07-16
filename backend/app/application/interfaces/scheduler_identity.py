from dataclasses import dataclass


@dataclass(frozen=True)
class SchedulerIdentity:
    key: str
    name: str

    def __post_init__(self) -> None:
        normalized_key = self.key.strip().lower()
        normalized_name = self.name.strip()

        if not normalized_key:
            raise ValueError("scheduler key cannot be empty")

        if not normalized_name:
            raise ValueError("scheduler name cannot be empty")

        object.__setattr__(
            self,
            "key",
            normalized_key,
        )

        object.__setattr__(
            self,
            "name",
            normalized_name,
        )
