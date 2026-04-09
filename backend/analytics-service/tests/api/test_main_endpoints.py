from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


@patch("src.main.disconnect_from_mongodb", new_callable=AsyncMock)
@patch("src.main.close_recipe_client", new_callable=AsyncMock)
@patch("src.main.connect_to_mongodb", new_callable=AsyncMock)
def test_root_endpoint(_mock_connect, _mock_close_recipe_client, _mock_disconnect):
    from src.main import app

    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Analytics Service is running"
    assert "version" in body


@patch("src.main.disconnect_from_mongodb", new_callable=AsyncMock)
@patch("src.main.close_recipe_client", new_callable=AsyncMock)
@patch("src.main.connect_to_mongodb", new_callable=AsyncMock)
def test_health_endpoint(_mock_connect, _mock_close_recipe_client, _mock_disconnect):
    from src.main import app

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "analytics-service"}
