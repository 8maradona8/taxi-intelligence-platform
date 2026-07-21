from datetime import timedelta

import pytest

from app.services.bus_signal_persistence_service import (
    BusSignalPersistenceService,
)


def make_payload() -> dict[str, object]:
    return {
        "mode": "bus",
        "station_code": ("sofia-central-bus-station"),
        "arrival_times": [
            "2026-07-20T10:30:00+03:00",
        ],
        "routes": [
            "ВАРНА - СОФИЯ",
        ],
        "carriers": [
            "ГЛОБАЛ БИОМЕТ ЕООД",
        ],
        "arrivals": 1,
        "unique_origins": 1,
        "known_sectors": 1,
    }


def test_bus_fingerprint_is_stable_for_same_payload() -> None:
    first = BusSignalPersistenceService._bus_payload_fingerprint(
        make_payload(),
    )

    second = BusSignalPersistenceService._bus_payload_fingerprint(
        make_payload(),
    )

    assert first == second


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        (
            "arrival_times",
            [
                "2026-07-20T10:45:00+03:00",
            ],
        ),
        (
            "routes",
            [
                "ДОБРИЧ - СОФИЯ",
            ],
        ),
        (
            "carriers",
            [
                "ЮНИОН - ИВКОНИ ООД",
            ],
        ),
        (
            "arrivals",
            2,
        ),
        (
            "unique_origins",
            2,
        ),
        (
            "known_sectors",
            0,
        ),
    ],
)
def test_bus_fingerprint_detects_relevant_changes(
    field: str,
    replacement: object,
) -> None:
    first_payload = make_payload()
    second_payload = make_payload()

    second_payload[field] = replacement

    first = BusSignalPersistenceService._bus_payload_fingerprint(
        first_payload,
    )

    second = BusSignalPersistenceService._bus_payload_fingerprint(
        second_payload,
    )

    assert first != second


def test_bus_persistence_rejects_invalid_deduplication_window() -> None:
    with pytest.raises(
        ValueError,
        match=("deduplication_window must be positive"),
    ):
        BusSignalPersistenceService(
            zone_repository=object(),  # type: ignore[arg-type]
            signal_repository=object(),  # type: ignore[arg-type]
            deduplication_window=timedelta(0),
        )
