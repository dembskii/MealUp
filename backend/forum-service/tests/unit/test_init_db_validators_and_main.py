import asyncio
import runpy
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src import init_posts as init_posts_module
from src.db import main as db_main
from src.validators.results import ErrorResponse, SuccessResponse
from tests.unit.fakes import FakeAsyncSession, FakeResult


def run(coro):
    return asyncio.run(coro)


def test_generate_mock_posts_creates_expected_count():
    posts = init_posts_module.generate_mock_posts(count=5)

    assert len(posts) == 5
    assert all(post.title for post in posts)
    assert all(post.content for post in posts)


def test_seed_posts_commits_in_batches(monkeypatch):
    posts = init_posts_module.generate_mock_posts(count=11)
    session = FakeAsyncSession()

    async def _embed(text):
        return [0.1, 0.2]

    monkeypatch.setattr(init_posts_module, "generate_embedding", _embed)

    run(init_posts_module.seed_posts(session, posts))

    assert session.commits == 2
    assert len(session.added) == 11


def test_seed_posts_handles_missing_embedding(monkeypatch):
    posts = init_posts_module.generate_mock_posts(count=1)
    session = FakeAsyncSession()

    async def _embed(text):
        return None

    monkeypatch.setattr(init_posts_module, "generate_embedding", _embed)

    run(init_posts_module.seed_posts(session, posts))

    assert session.commits == 1
    assert posts[0].embedding is None


def test_init_posts_skips_when_data_exists(monkeypatch):
    session = FakeAsyncSession(exec_plan=[FakeResult(first=SimpleNamespace(id=uuid4()))])

    class _Ctx:
        async def __aenter__(self):
            return session

        async def __aexit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(init_posts_module, "AsyncSession", lambda _engine: _Ctx())
    seed_mock = AsyncMock()
    monkeypatch.setattr(init_posts_module, "seed_posts", seed_mock)

    run(init_posts_module.init_posts())

    seed_mock.assert_not_awaited()


def test_init_posts_seeds_when_table_empty(monkeypatch):
    session = FakeAsyncSession(exec_plan=[FakeResult(first=None)])

    class _Ctx:
        async def __aenter__(self):
            return session

        async def __aexit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(init_posts_module, "AsyncSession", lambda _engine: _Ctx())
    fake_posts = [SimpleNamespace(id=uuid4())]
    monkeypatch.setattr(init_posts_module, "generate_mock_posts", lambda count=100: fake_posts)
    seed_mock = AsyncMock()
    monkeypatch.setattr(init_posts_module, "seed_posts", seed_mock)

    run(init_posts_module.init_posts())

    seed_mock.assert_awaited_once_with(session, fake_posts)


def test_get_session_yields_session(monkeypatch):
    fake_session = object()

    class _Ctx:
        async def __aenter__(self):
            return fake_session

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class _Maker:
        def __call__(self):
            return _Ctx()

    monkeypatch.setattr(db_main, "sessionmaker", lambda **kwargs: _Maker())

    async def _consume():
        gen = db_main.get_session()
        yielded = await gen.__anext__()
        with pytest.raises(StopAsyncIteration):
            await gen.__anext__()
        return yielded

    yielded = run(_consume())
    assert yielded is fake_session


def test_results_validators_schema_and_values():
    success = SuccessResponse(message="ok")
    error = ErrorResponse(detail="not found", status_code=404)

    assert success.message == "ok"
    assert error.status_code == 404

    schema = SuccessResponse.model_json_schema()
    assert schema["properties"]["message"]["description"] == "Success message"


def test_main_module_runs_uvicorn_in_script_mode(monkeypatch):
    called = {}

    def _run(app, host, port):
        called["host"] = host
        called["port"] = port
        called["app"] = app

    fake_uvicorn = SimpleNamespace(run=_run)
    monkeypatch.setitem(sys.modules, "uvicorn", fake_uvicorn)

    runpy.run_module("src.main", run_name="__main__")

    assert called["host"] == "0.0.0.0"
    assert called["port"] == 8007
