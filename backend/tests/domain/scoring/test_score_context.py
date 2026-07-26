from datetime import UTC, datetime, timedelta, timezone

import pytest

from app.domain.scoring import ScoreContext


def test_score_context_exposes_attributes() -> None:
    context = ScoreContext(
        subject=" weather ",
        observed_at=datetime(
            2026,
            7,
            22,
            12,
            0,
            tzinfo=UTC,
        ),
        attributes={
            "temperature": 18.5,
            "condition": "rain",
        },
    )

    assert context.subject == "weather"
    assert context.get("temperature") == 18.5
    assert context.require("condition") == "rain"
    assert context.get("missing", 42) == 42


def test_score_context_normalizes_observed_at_to_utc() -> None:
    sofia_timezone = timezone(timedelta(hours=3))

    context = ScoreContext(
        subject="weather",
        observed_at=datetime(
            2026,
            7,
            22,
            15,
            0,
            tzinfo=sofia_timezone,
        ),
    )

    assert context.observed_at == datetime(
        2026,
        7,
        22,
        12,
        0,
        tzinfo=UTC,
    )


def test_score_context_requires_timezone_aware_datetime() -> None:
    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        ScoreContext(
            subject="weather",
            observed_at=datetime(
                2026,
                7,
                22,
                12,
                0,
            ),
        )


def test_score_context_require_rejects_missing_attribute() -> None:
    context = ScoreContext(subject="weather")

    with pytest.raises(
        KeyError,
        match="precipitation",
    ):
        context.require("precipitation")
