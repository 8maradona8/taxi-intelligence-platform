from datetime import UTC, datetime, timedelta

from app.application.demand_fusion import (
    ZoneSignalGrouper,
)
from app.domain.demand_fusion import (
    DemandSignalInput,
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
    zone_name: str,
    source: SignalSource,
    signal_type: SignalType,
) -> DemandSignalInput:
    return DemandSignalInput(
        source=source,
        signal_type=signal_type,
        zone_name=zone_name,
        score=70.0,
        confidence=0.8,
        observed_at=OBSERVED_AT,
        expires_at=(OBSERVED_AT + timedelta(minutes=30)),
    )


def test_grouper_groups_signals_by_zone() -> None:
    airport_activity = make_signal(
        zone_name="Sofia Airport",
        source=SignalSource.AIRPORT,
        signal_type=SignalType.AIRPORT_ACTIVITY,
    )
    airport_weather = make_signal(
        zone_name="Sofia Airport",
        source=SignalSource.WEATHER,
        signal_type=SignalType.WEATHER_CONDITION,
    )
    center_event = make_signal(
        zone_name="Sofia Center",
        source=SignalSource.EVENTS,
        signal_type=SignalType.EVENT_ACTIVITY,
    )

    groups = ZoneSignalGrouper().group(
        (
            airport_activity,
            center_event,
            airport_weather,
        )
    )

    assert len(groups) == 2

    assert groups[0].zone_name == "Sofia Airport"
    assert groups[0].signals == (
        airport_activity,
        airport_weather,
    )

    assert groups[1].zone_name == "Sofia Center"
    assert groups[1].signals == (center_event,)


def test_grouper_preserves_first_zone_appearance_order() -> None:
    center = make_signal(
        zone_name="Sofia Center",
        source=SignalSource.EVENTS,
        signal_type=SignalType.EVENT_ACTIVITY,
    )
    airport = make_signal(
        zone_name="Sofia Airport",
        source=SignalSource.AIRPORT,
        signal_type=SignalType.AIRPORT_ACTIVITY,
    )
    center_weather = make_signal(
        zone_name="Sofia Center",
        source=SignalSource.WEATHER,
        signal_type=SignalType.WEATHER_CONDITION,
    )

    groups = ZoneSignalGrouper().group(
        (
            center,
            airport,
            center_weather,
        )
    )

    assert tuple(group.zone_name for group in groups) == (
        "Sofia Center",
        "Sofia Airport",
    )


def test_grouper_preserves_signal_order_inside_zone() -> None:
    first = make_signal(
        zone_name="Sofia Center",
        source=SignalSource.EVENTS,
        signal_type=SignalType.EVENT_ACTIVITY,
    )
    second = make_signal(
        zone_name="Sofia Center",
        source=SignalSource.WEATHER,
        signal_type=SignalType.WEATHER_CONDITION,
    )
    third = make_signal(
        zone_name="Sofia Center",
        source=SignalSource.TRAFFIC,
        signal_type=SignalType.TRAFFIC_CONDITION,
    )

    groups = ZoneSignalGrouper().group(
        (
            first,
            second,
            third,
        )
    )

    assert groups[0].signals == (
        first,
        second,
        third,
    )


def test_grouper_returns_immutable_empty_result() -> None:
    result = ZoneSignalGrouper().group(())

    assert result == ()
    assert isinstance(result, tuple)


def test_grouper_does_not_filter_expired_signals() -> None:
    expired = DemandSignalInput(
        source=SignalSource.WEATHER,
        signal_type=SignalType.WEATHER_CONDITION,
        zone_name="Sofia Center",
        score=70.0,
        confidence=0.8,
        observed_at=(OBSERVED_AT - timedelta(hours=2)),
        expires_at=(OBSERVED_AT - timedelta(hours=1)),
    )

    groups = ZoneSignalGrouper().group((expired,))

    assert groups[0].signals == (expired,)
