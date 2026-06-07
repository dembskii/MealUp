import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

# Ensure imports work for shared backend/common package.
BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Ensure required settings exist before importing app/config modules.
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_USER_DB", "test")
os.environ.setdefault("USER_DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("AUTH_REDIS_PASSWORD", "test")
os.environ.setdefault("REDIS_AUTH_URL", "redis://localhost:6379")
os.environ.setdefault("AUTH0_DOMAIN", "example.auth0.com")
os.environ.setdefault("AUTH0_AUDIENCE", "mealup-api")
os.environ.setdefault("ALGORITHMS", "RS256")

import src.api.routes as routes
import src.main as main_module


@pytest.fixture
def session_mock() -> AsyncMock:
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.rollback = AsyncMock()
    session.delete = AsyncMock()
    session.exec = AsyncMock()
    return session


@pytest.fixture
def client(session_mock: AsyncMock) -> TestClient:
    async def _session_override():
        yield session_mock

    async def _auth_override():
        return {"sub": "test-user"}

    main_module.app.dependency_overrides[routes.get_session] = _session_override
    main_module.app.dependency_overrides[routes.require_auth] = _auth_override

    with TestClient(main_module.app) as test_client:
        yield test_client

    main_module.app.dependency_overrides.clear()
