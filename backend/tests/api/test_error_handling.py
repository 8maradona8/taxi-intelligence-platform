from fastapi.testclient import TestClient


def test_unknown_route_returns_structured_error(
    api_client: TestClient,
) -> None:
    response = api_client.get("/api/v1/does-not-exist")

    assert response.status_code == 404

    data = response.json()
    error = data["error"]

    assert error["code"] == "NOT_FOUND"
    assert error["message"] == "Not Found"
    assert error["request_id"]
    assert error["timestamp"]
    assert error["details"] is None


def test_request_id_is_preserved(
    api_client: TestClient,
) -> None:
    request_id = "tip-pytest-request-123"

    response = api_client.get(
        "/api/v1/cities/Sofia/snapshot",
        headers={
            "X-Request-ID": request_id,
        },
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id
