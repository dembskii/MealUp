import os
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

# Ensure settings can be initialized in tests.
os.environ.setdefault("WORKOUT_MONGODB_URL", "mongodb://mocked-mongo:27017")

import src.main as main_app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """FastAPI test client with Mongo lifecycle mocked out."""
    monkeypatch.setattr(main_app, "connect_to_mongodb", AsyncMock())
    monkeypatch.setattr(main_app, "disconnect_from_mongodb", AsyncMock())

    with TestClient(main_app.app) as test_client:
        yield test_client
