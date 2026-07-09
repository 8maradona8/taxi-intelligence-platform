from enum import StrEnum


class DecisionAction(StrEnum):
    WAIT = "wait"
    MOVE = "move"
    AVOID = "avoid"