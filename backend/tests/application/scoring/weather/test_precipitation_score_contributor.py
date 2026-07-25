from datetime import datetime

import pytest

from app.application.scoring import ScoreContributor
from app.application.scoring.weather import (
    PrecipitationScoreContributor,
)
from app.domain.scoring import ScoreContext
from tests.application.scoring.weather.conftest import (
    make_weather_context,
)


def test_precipitation_contributor_satisfies_protocol() -> None:
    assert isinstance(
        PrecipitationScoreContributor(),
        ScoreContributor,
    )


@pytest.mark.parametrize(
    (
        "precipitation_amount_mm",
        "expected_score",
        "expected_code",
    ),
    [
        (
            0.0,
            10.0,
            "weather_no_precipitation",
        ),
        (
            0.01,
            35.0,
            "weather_light_precipitation",
        ),
        (
            0.5,
            35.0,
            "weather_light_precipitation",
        ),
        (
            0.5001,
            60.0,
            "weather_moderate_precipitation",
        ),
        (
            2.0,
            60.0,
            "weather_moderate_precipitation",
        ),
        (
            2.0001,
            80.0,
            "weather_heavy_precipitation",
        ),
        (
            5.0,
            80.0,
            "weather_heavy_precipitation",
        ),
        (
            5.0001,
            95.0,
            "weather_extreme_precipitation",
        ),
    ],
)
def test_precipitation_amount_thresholds(
    observed_at: datetime,
    precipitation_amount_mm: float,
    expected_score: float,
    expected_code: str,
) -> None:
    context = make_weather_context(
        observed_at=observed_at,
        precipitation_amount_mm=precipitation_amount_mm,
        symbol_code="rain",
    )

    contribution = PrecipitationScoreContributor().evaluate(
        context,
    )

    assert contribution.contributor == "weather_precipitation"
    assert contribution.score == expected_score
    assert contribution.reason.code == expected_code


@pytest.mark.parametrize(
    (
        "symbol_code",
        "precipitation_amount_mm",
        "expected_score",
        "expected_code",
    ),
    [
        (
            "snow",
            0.1,
            85.0,
            "weather_snow",
        ),
        (
            "sleet",
            0.1,
            90.0,
            "weather_sleet_or_mixed_precipitation",
        ),
        (
            "rainandsnow",
            0.1,
            90.0,
            "weather_sleet_or_mixed_precipitation",
        ),
        (
            "heavyrainandthunder",
            1.0,
            95.0,
            "weather_thunderstorm",
        ),
    ],
)
def test_precipitation_condition_overrides(
    observed_at: datetime,
    symbol_code: str,
    precipitation_amount_mm: float,
    expected_score: float,
    expected_code: str,
) -> None:
    context = make_weather_context(
        observed_at=observed_at,
        symbol_code=symbol_code,
        precipitation_amount_mm=precipitation_amount_mm,
    )

    contribution = PrecipitationScoreContributor().evaluate(
        context,
    )

    assert contribution.score == expected_score
    assert contribution.reason.code == expected_code


def test_precipitation_contribution_contains_metadata(
    observed_at: datetime,
) -> None:
    contribution = PrecipitationScoreContributor().evaluate(
        make_weather_context(
            observed_at=observed_at,
            precipitation_amount_mm=3.0,
            symbol_code="rain",
        )
    )

    assert contribution.weight == 0.50
    assert contribution.confidence == 0.95
    assert contribution.metadata["location"] == "Sofia"
    assert contribution.metadata["provider"] == "met-norway"
    assert contribution.metadata["precipitation_amount_mm"] == 3.0
    assert contribution.reason.metadata["precipitation_type"] == "rain"


def test_precipitation_contributor_requires_snapshot(
    observed_at: datetime,
) -> None:
    context = ScoreContext(
        subject="weather",
        observed_at=observed_at,
    )

    with pytest.raises(
        KeyError,
        match="weather_snapshot",
    ):
        PrecipitationScoreContributor().evaluate(context)


def test_precipitation_contributor_rejects_invalid_snapshot_type(
    observed_at: datetime,
) -> None:
    context = ScoreContext(
        subject="weather",
        observed_at=observed_at,
        attributes={
            "weather_snapshot": "invalid",
        },
    )

    with pytest.raises(
        TypeError,
        match="must be a WeatherSnapshot",
    ):
        PrecipitationScoreContributor().evaluate(context)
