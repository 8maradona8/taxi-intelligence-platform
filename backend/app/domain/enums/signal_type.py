from enum import StrEnum


class SignalType(StrEnum):
    AIRPORT_ACTIVITY = "airport_activity"
    WEATHER_CONDITION = "weather_condition"
    TRAFFIC_CONDITION = "traffic_condition"
    EVENT_ACTIVITY = "event_activity"
    TRANSPORT_ACTIVITY = "transport_activity"
