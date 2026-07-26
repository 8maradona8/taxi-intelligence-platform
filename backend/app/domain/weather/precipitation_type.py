from enum import StrEnum


class PrecipitationType(StrEnum):
    """Provider-neutral precipitation type."""

    NONE = "none"
    RAIN = "rain"
    SNOW = "snow"
    SLEET = "sleet"
    MIXED = "mixed"
    UNKNOWN = "unknown"

    @classmethod
    def from_symbol_code(
        cls,
        symbol_code: str,
        *,
        precipitation_amount_mm: float = 0.0,
    ) -> "PrecipitationType":
        normalized_code = symbol_code.strip().lower()

        has_rain = "rain" in normalized_code
        has_snow = "snow" in normalized_code

        if "sleet" in normalized_code:
            return cls.SLEET

        if has_rain and has_snow:
            return cls.MIXED

        if has_snow:
            return cls.SNOW

        if has_rain:
            return cls.RAIN

        if precipitation_amount_mm <= 0.0:
            return cls.NONE

        return cls.UNKNOWN
