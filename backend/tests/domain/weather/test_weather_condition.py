import pytest

from app.domain.weather import WeatherCondition


@pytest.mark.parametrize(
    ("symbol_code", "expected"),
    [
        ("clearsky_day", WeatherCondition.CLEAR),
        ("clearsky_night", WeatherCondition.CLEAR),
        ("fair_day", WeatherCondition.PARTLY_CLOUDY),
        (
            "partlycloudy_day",
            WeatherCondition.PARTLY_CLOUDY,
        ),
        ("cloudy", WeatherCondition.CLOUDY),
        ("fog", WeatherCondition.FOG),
        ("rain", WeatherCondition.RAIN),
        ("rainshowers_day", WeatherCondition.RAIN),
        ("snow", WeatherCondition.SNOW),
        ("sleet", WeatherCondition.SLEET),
        (
            "heavyrainandthunder",
            WeatherCondition.THUNDERSTORM,
        ),
        (
            "unknown-provider-code",
            WeatherCondition.UNKNOWN,
        ),
        ("", WeatherCondition.UNKNOWN),
    ],
)
def test_maps_symbol_code_to_weather_condition(
    symbol_code: str,
    expected: WeatherCondition,
) -> None:
    assert WeatherCondition.from_symbol_code(symbol_code) == expected
