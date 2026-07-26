from datetime import UTC, datetime, timedelta

import pytest

from app.application.scoring.weather import (
    WeatherForecastWindowAssessment,
    WeatherScoreService,
)
from app.domain.weather import (
    WeatherForecast,
    WeatherSnapshot,
)


def make_forecast(
    *,
    forecast_at: datetime,
    temperature: float = 20.0,
    wind_speed: float = 2.0,
    precipitation: float = 0.0,
    symbol_code: str = "clearsky_day",
) -> WeatherForecast:
    return WeatherForecast(
        forecast_at=forecast_at,
        air_temperature_celsius=temperature,
        relative_humidity_percent=60.0,
        wind_speed_mps=wind_speed,
        wind_from_direction_degrees=180.0,
        cloud_area_fraction_percent=20.0,
        air_pressure_at_sea_level_hpa=1015.0,
        precipitation_amount_mm=precipitation,
        symbol_code=symbol_code,
    )


def test_assess_forecast_window_scores_each_relevant_forecast() -> None:
    observed_at = datetime(
        2026,
        7,
        26,
        12,
        0,
        tzinfo=UTC,
    )
    snapshot = WeatherSnapshot.create(
        observed_at=observed_at,
        forecasts=[
            make_forecast(
                forecast_at=observed_at,
            ),
            make_forecast(
                forecast_at=observed_at + timedelta(hours=1),
                wind_speed=5.0,
            ),
            make_forecast(
                forecast_at=observed_at + timedelta(hours=2),
                temperature=4.0,
                wind_speed=12.0,
                precipitation=2.5,
                symbol_code="heavyrain",
            ),
            make_forecast(
                forecast_at=observed_at + timedelta(hours=8),
                precipitation=4.0,
                symbol_code="heavyrain",
            ),
        ],
    )

    result = WeatherScoreService().assess_forecast_window(
        snapshot,
        window=timedelta(hours=6),
    )

    assert isinstance(
        result,
        WeatherForecastWindowAssessment,
    )
    assert result.window_minutes == 360
    assert result.forecast_count == 3
    assert [item.horizon_minutes for item in result.assessments] == [0, 60, 120]
    assert result.peak.forecast_at == (observed_at + timedelta(hours=2))
    assert result.peak.assessment.score == pytest.approx(
        71.73,
        abs=0.01,
    )


def test_assess_forecast_window_falls_back_to_current_forecast() -> None:
    observed_at = datetime(
        2026,
        7,
        26,
        12,
        0,
        tzinfo=UTC,
    )
    forecast_at = observed_at + timedelta(hours=8)
    snapshot = WeatherSnapshot.create(
        observed_at=observed_at,
        forecasts=[
            make_forecast(
                forecast_at=forecast_at,
            )
        ],
    )

    result = WeatherScoreService().assess_forecast_window(
        snapshot,
        window=timedelta(hours=6),
    )

    assert result.forecast_count == 1
    assert result.peak.forecast_at == forecast_at
    assert result.peak.horizon_minutes == 480


def test_assess_forecast_window_rejects_non_positive_window() -> None:
    observed_at = datetime(
        2026,
        7,
        26,
        12,
        0,
        tzinfo=UTC,
    )
    snapshot = WeatherSnapshot.create(
        observed_at=observed_at,
        forecasts=[
            make_forecast(
                forecast_at=observed_at,
            )
        ],
    )

    with pytest.raises(
        ValueError,
        match="window must be positive",
    ):
        WeatherScoreService().assess_forecast_window(
            snapshot,
            window=timedelta(0),
        )
