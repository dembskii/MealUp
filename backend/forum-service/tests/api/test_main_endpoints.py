from fastapi.testclient import TestClient


def test_root_endpoint():
    from src.main import app

    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Forum Service is running"
    assert "version" in body


def test_health_endpoint():
    from src.main import app

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "forum-service"}
