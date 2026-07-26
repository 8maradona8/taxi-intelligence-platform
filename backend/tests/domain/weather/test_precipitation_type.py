import pytest

from app.domain.weather import PrecipitationType


@pytest.mark.parametrize(
    (
        "symbol_code",
        "precipitation_amount_mm",
        "expected",
    ),
    [
        ("clearsky_day", 0.0, PrecipitationType.NONE),
        ("rain", 1.0, PrecipitationType.RAIN),
        ("snow", 1.0, PrecipitationType.SNOW),
        ("sleet", 1.0, PrecipitationType.SLEET),
        (
            "rainandsnow",
            1.0,
            PrecipitationType.MIXED,
        ),
        (
            "unknown-provider-code",
            2.0,
            PrecipitationType.UNKNOWN,
        ),
        (
            "unknown-provider-code",
            0.0,
            PrecipitationType.NONE,
        ),
    ],
)
def test_maps_symbol_code_to_precipitation_type(
    symbol_code: str,
    precipitation_amount_mm: float,
    expected: PrecipitationType,
) -> None:
    result = PrecipitationType.from_symbol_code(
        symbol_code,
        precipitation_amount_mm=(precipitation_amount_mm),
    )

    assert result == expected
