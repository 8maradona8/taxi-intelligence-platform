from enum import StrEnum


class TrainStatus(StrEnum):
    SCHEDULED = "scheduled"
    EXPECTED = "expected"
    DELAYED = "delayed"
    EARLY = "early"
    CANCELLED = "cancelled"
    ARRIVED = "arrived"
    UNKNOWN = "unknown"
