from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "version" in response.json()

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_status():
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    assert response.json()["status"] == "Gateway is operational"

def test_services():
    response = client.get("/api/v1/services")
    assert response.status_code == 200
    assert "auth_service" in response.json()
    assert "user_service" in response.json()