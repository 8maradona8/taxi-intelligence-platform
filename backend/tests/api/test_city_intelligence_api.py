from fastapi.testclient import TestClient


def test_snapshot_endpoint_returns_city_snapshot(
    api_client: TestClient,
) -> None:
    response = api_client.get("/api/v1/cities/Sofia/snapshot")

    assert response.status_code == 200

    data = response.json()

    assert data["city_name"] == "Sofia"
    assert len(data["opportunities"]) == 2
    assert data["best_recommendation"]["zone_name"] == "Sofia Airport"
    assert data["best_recommendation"]["action"] == "move"


def test_opportunities_endpoint_returns_ranked_zones(
    api_client: TestClient,
) -> None:
    response = api_client.get("/api/v1/cities/Sofia/opportunities")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    assert data[0]["rank"] == 1
    assert data[0]["zone_name"] == "Sofia Airport"
    assert data[0]["score"] == 148.5

    assert data[1]["rank"] == 2
    assert data[1]["zone_name"] == "NDK"
    assert data[1]["score"] == 117.6


def test_recommendation_endpoint_returns_best_action(
    api_client: TestClient,
) -> None:
    response = api_client.get("/api/v1/cities/Sofia/recommendation")

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Move to Sofia Airport"
    assert data["summary"] == "MOVE to Sofia Airport"
    assert data["zone_name"] == "Sofia Airport"
    assert data["action"] == "move"
    assert data["urgency"] == "high"
    assert data["confidence"] == 92
