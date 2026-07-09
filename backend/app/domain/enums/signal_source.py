from enum import StrEnum


class SignalSource(StrEnum):
    AIRPORT = "airport"
    WEATHER = "weather"
    TRAFFIC = "traffic"
    EVENTS = "events"
    TRANSPORT = "transport"