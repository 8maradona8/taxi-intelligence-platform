from datetime import UTC, datetime

from app.application.dto import AirportSignalHistoryResponse
from app.models.signal import Signal


def test_history_response_maps_signal_model() -> None:
    signal = Signal(
        id=10,
        signal_type="airport_activity",
        source="airport",
        zone_id=1,
        impact_score=48.0,
        observed_at=datetime(
            2026,
            7,
            13,
            12,
            0,
            tzinfo=UTC,
        ),
        payload={
            "airport": "SOF",
            "arrivals": 4,
            "scheduled": 2,
            "expected": 1,
            "delayed": 1,
            "cancelled": 0,
            "confidence": 0.95,
            "priority": "medium",
            "flight_numbers": [
                "FR100",
                "W6100",
            ],
            "terminal_distribution": {
                "Terminal 1": 1,
                "Terminal 2": 3,
            },
        },
    )

    signal.created_at = datetime(
        2026,
        7,
        13,
        12,
        1,
        tzinfo=UTC,
    )

    response = AirportSignalHistoryResponse.from_models([signal])

    assert response.airport == "SOF"
    assert response.count == 1

    item = response.signals[0]

    assert item.id == 10
    assert item.impact_score == 48.0
    assert item.arrivals == 4
    assert item.delayed == 1
    assert item.confidence == 0.95
    assert item.priority == "medium"
    assert item.flight_numbers == [
        "FR100",
        "W6100",
    ]
