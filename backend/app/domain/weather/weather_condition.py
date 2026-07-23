from enum import StrEnum


class WeatherCondition(StrEnum):
    """Provider-neutral weather condition."""

    CLEAR = "clear"
    PARTLY_CLOUDY = "partly_cloudy"
    CLOUDY = "cloudy"
    FOG = "fog"
    RAIN = "rain"
    SNOW = "snow"
    SLEET = "sleet"
    THUNDERSTORM = "thunderstorm"
    UNKNOWN = "unknown"

    @classmethod
    def from_symbol_code(
        cls,
        symbol_code: str,
    ) -> "WeatherCondition":
        normalized_code = symbol_code.strip().lower()

        if not normalized_code:
            return cls.UNKNOWN

        if "thunder" in normalized_code:
            return cls.THUNDERSTORM

        if "sleet" in normalized_code:
            return cls.SLEET

        if "snow" in normalized_code:
            return cls.SNOW

        if "rain" in normalized_code:
            return cls.RAIN

        if "fog" in normalized_code:
            return cls.FOG

        if normalized_code.startswith("clearsky"):
            return cls.CLEAR

        if normalized_code.startswith(
            (
                "fair",
                "partlycloudy",
            )
        ):
            return cls.PARTLY_CLOUDY

        if "cloudy" in normalized_code:
            return cls.CLOUDY

        return cls.UNKNOWN
