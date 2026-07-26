from datetime import UTC, datetime, timedelta

import pytest

from app.domain.demand_fusion import (
    DemandSignalInput,
    ZoneSignalGroup,
)
from app.domain.enums import (
    SignalSource,
    SignalType,
)


OBSERVED_AT = datetime(
    2026,
    7,
    26,
    12,
    0,
    tzinfo=UTC,
)


def make_signal(
    *,
    zone_name: str = "Sofia Center",
) -> DemandSignalInput:
    return DemandSignalInput(
        source=SignalSource.WEATHER,
        signal_type=SignalType.WEATHER_CONDITION,
        zone_name=zone_name,
        score=70.0,
        confidence=0.8,
        observed_at=OBSERVED_AT,
        expires_at=(OBSERVED_AT + timedelta(minutes=30)),
    )


def test_zone_signal_group_exposes_signal_count() -> None:
    first = make_signal()
    second = make_signal()

    group = ZoneSignalGroup(
        zone_name="Sofia Center",
        signals=(
            first,
            second,
        ),
    )

    assert group.zone_name == "Sofia Center"
    assert group.signals == (
        first,
        second,
    )
    assert group.signal_count == 2


def test_zone_signal_group_normalizes_zone_name() -> None:
    signal = make_signal(
        zone_name="Sofia Center",
    )

    group = ZoneSignalGroup(
        zone_name="  Sofia Center  ",
        signals=(signal,),
    )

    assert group.zone_name == "Sofia Center"


def test_zone_signal_group_rejects_empty_signals() -> None:
    with pytest.raises(
        ValueError,
        match="signals cannot be empty",
    ):
        ZoneSignalGroup(
            zone_name="Sofia Center",
            signals=(),
        )


def test_zone_signal_group_rejects_mixed_zones() -> None:
    center = make_signal(
        zone_name="Sofia Center",
    )
    airport = make_signal(
        zone_name="Sofia Airport",
    )

    with pytest.raises(
        ValueError,
        match="must belong to the group zone",
    ):
        ZoneSignalGroup(
            zone_name="Sofia Center",
            signals=(
                center,
                airport,
            ),
        )
