import os
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Ensure package roots are importable for `src` and shared `common` modules.
SERVICE_ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_ROOT_DIR = Path(__file__).resolve().parents[2]

for path in (SERVICE_ROOT_DIR, BACKEND_ROOT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


# Ensure required settings exist before importing app modules.
ENV_DEFAULTS = {
    "POSTGRES_USER": "test",
    "POSTGRES_PASSWORD": "test",
    "POSTGRES_FORUM_DB": "forum_test",
    "FORUM_DATABASE_URL": "postgresql+asyncpg://test:test@localhost:5432/forum_test",
    "RECIPE_SERVICE_URL": "http://localhost:8005",
    "WORKOUT_SERVICE_URL": "http://localhost:8006",
    "USER_SERVICE_URL": "http://localhost:8004",
    "AUTH_REDIS_PASSWORD": "test",
    "REDIS_AUTH_URL": "redis://localhost:6379/0",
    "AUTH0_DOMAIN": "test.auth0.com",
    "AUTH0_AUDIENCE": "test-audience",
    "ALGORITHMS": "RS256",
    "EMBEDDING_MODEL": "text-embedding-3-small",
    "RETRIEVE_LLM": "openai/gpt-4o-mini",
    "OPENROUTER_API_KEY": "test-key",
    "OPENROUTER_BASE_URL": "https://openrouter.ai/api/v1",
}

for key, value in ENV_DEFAULTS.items():
    os.environ.setdefault(key, value)

from src.api import ai as ai_routes  # noqa: E402
from src.api import comments as comment_routes  # noqa: E402
from src.api import posts as post_routes  # noqa: E402
from src.api import search as search_routes  # noqa: E402


@pytest.fixture
def default_user_id() -> str:
    return "11111111-1111-1111-1111-111111111111"


@pytest.fixture
def auth_override(default_user_id: str) -> dict:
    return {
        "sub": default_user_id,
        "internal_uid": default_user_id,
    }


@pytest.fixture
def session_override() -> object:
    return object()


@pytest.fixture
def api_app(auth_override: dict, session_override: object) -> FastAPI:
    app = FastAPI()
    app.include_router(post_routes.router, prefix="/forum", tags=["posts"])
    app.include_router(comment_routes.router, prefix="/forum", tags=["comments"])
    app.include_router(search_routes.router, prefix="/forum", tags=["search"])
    app.include_router(ai_routes.router, prefix="/forum", tags=["ai"])

    app.dependency_overrides[post_routes.require_auth] = lambda: auth_override
    app.dependency_overrides[comment_routes.require_auth] = lambda: auth_override
    app.dependency_overrides[search_routes.require_auth] = lambda: auth_override
    app.dependency_overrides[ai_routes.require_auth] = lambda: auth_override

    app.dependency_overrides[post_routes.get_session] = lambda: session_override
    app.dependency_overrides[comment_routes.get_session] = lambda: session_override
    app.dependency_overrides[search_routes.get_session] = lambda: session_override
    app.dependency_overrides[ai_routes.get_session] = lambda: session_override

    return app


@pytest.fixture
def client(api_app: FastAPI):
    with TestClient(api_app) as test_client:
        yield test_client
