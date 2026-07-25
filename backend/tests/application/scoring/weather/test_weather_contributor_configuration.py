import pytest

from app.application.scoring.weather import (
    PrecipitationScoreContributor,
    TemperatureScoreContributor,
    WindScoreContributor,
)


CONTRIBUTORS = (
    PrecipitationScoreContributor,
    TemperatureScoreContributor,
    WindScoreContributor,
)


@pytest.mark.parametrize(
    "contributor_type",
    CONTRIBUTORS,
)
@pytest.mark.parametrize(
    "weight",
    [
        0.0,
        -0.1,
    ],
)
def test_weather_contributors_reject_invalid_weight(
    contributor_type: type[
        PrecipitationScoreContributor
        | TemperatureScoreContributor
        | WindScoreContributor
    ],
    weight: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="weight must be greater than 0.0",
    ):
        contributor_type(weight=weight)


@pytest.mark.parametrize(
    "contributor_type",
    CONTRIBUTORS,
)
@pytest.mark.parametrize(
    "confidence",
    [
        -0.01,
        1.01,
    ],
)
def test_weather_contributors_reject_invalid_confidence(
    contributor_type: type[
        PrecipitationScoreContributor
        | TemperatureScoreContributor
        | WindScoreContributor
    ],
    confidence: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="confidence must be between",
    ):
        contributor_type(confidence=confidence)
