from app.application.interfaces.scheduler_identity import (
    SchedulerIdentity,
)


AIRPORT_SCHEDULER = SchedulerIdentity(
    key="airport",
    name="airport-signal-scheduler",
)

BUS_SCHEDULER = SchedulerIdentity(
    key="bus",
    name="bus-signal-scheduler",
)

RAILWAY_SCHEDULER = SchedulerIdentity(
    key="railway",
    name="railway-signal-scheduler",
)

WEATHER_SCHEDULER = SchedulerIdentity(
    key="weather",
    name="weather-signal-scheduler",
)
