from enum import StrEnum


class FlightStatus(StrEnum):
    SCHEDULED = "scheduled"
    EXPECTED = "expected"
    LANDED = "landed"
    DELAYED = "delayed"
    CANCELLED = "cancelled"
    DIVERTED = "diverted"
    UNKNOWN = "unknown"
