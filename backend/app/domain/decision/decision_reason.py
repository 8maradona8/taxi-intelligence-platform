from dataclasses import dataclass


@dataclass(frozen=True)
class DecisionReason:
    source: str
    description: str
    contribution: float