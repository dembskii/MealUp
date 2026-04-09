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
os.environ.setdefault("ANALYTICS_MONGODB_URL", "mongodb://localhost:27017")
os.environ.setdefault("RECIPE_SERVICE_URL", "http://localhost:8005")
os.environ.setdefault("AUTH0_DOMAIN", "test.auth0.com")
os.environ.setdefault("AUTH0_AUDIENCE", "test-audience")
os.environ.setdefault("ALGORITHMS", "RS256")

from src.api.routes import require_auth, router  # noqa: E402


@pytest.fixture
def auth_override():
    return {"sub": "test-user-sub"}


@pytest.fixture
def api_app(auth_override):
    app = FastAPI()
    app.include_router(router, prefix="/analytics", tags=["Analytics"])
    app.dependency_overrides[require_auth] = lambda: auth_override
    return app


@pytest.fixture
def client(api_app):
    with TestClient(api_app) as test_client:
        yield test_client
