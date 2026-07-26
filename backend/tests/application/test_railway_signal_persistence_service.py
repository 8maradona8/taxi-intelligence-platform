from app.services.railway_signal_persistence_service import (
    RailwaySignalPersistenceService,
)


def test_railway_fingerprint_detects_relevant_changes() -> None:
    first = RailwaySignalPersistenceService._railway_payload_fingerprint(
        {
            "mode": "railway",
            "station_code": "sofia-central",
            "train_numbers": ["2626"],
            "arrivals": 1,
            "delayed": 0,
            "early": 0,
            "total_positive_delay_minutes": 0,
        }
    )

    second = RailwaySignalPersistenceService._railway_payload_fingerprint(
        {
            "mode": "railway",
            "station_code": "sofia-central",
            "train_numbers": ["2626"],
            "arrivals": 1,
            "delayed": 1,
            "early": 0,
            "total_positive_delay_minutes": 20,
        }
    )

    assert first != second
