from app.application.handlers import GetCitySnapshotHandler
from app.application.queries import GetCitySnapshotQuery


def test_handler_returns_sofia_snapshot(
    snapshot_handler: GetCitySnapshotHandler,
) -> None:
    query = GetCitySnapshotQuery(
        city_name="Sofia",
    )

    snapshot = snapshot_handler.handle(query)

    assert snapshot.city_name == "Sofia"
    assert snapshot.opportunity_count == 2
    assert snapshot.has_recommendation is True

    recommendation = snapshot.best_recommendation

    assert recommendation is not None
    assert recommendation.zone_name == "Sofia Airport"
    assert recommendation.summary == "MOVE to Sofia Airport"

    assert snapshot.opportunities[0].zone_name == "Sofia Airport"
    assert snapshot.opportunities[1].zone_name == "NDK"
