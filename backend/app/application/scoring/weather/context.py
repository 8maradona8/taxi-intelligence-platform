from app.domain.scoring import ScoreContext
from app.domain.weather import WeatherSnapshot


WEATHER_SNAPSHOT_ATTRIBUTE = "weather_snapshot"


def require_weather_snapshot(
    context: ScoreContext,
) -> WeatherSnapshot:
    snapshot = context.require(WEATHER_SNAPSHOT_ATTRIBUTE)

    if not isinstance(snapshot, WeatherSnapshot):
        raise TypeError("weather_snapshot scoring attribute must be a WeatherSnapshot")

    return snapshot
