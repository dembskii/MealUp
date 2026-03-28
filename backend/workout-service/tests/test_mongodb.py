from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest

import src.db.mongodb as mongodb


@pytest.mark.asyncio
async def test_connect_disconnect_success(monkeypatch: pytest.MonkeyPatch):
    client = MagicMock()
    client.admin.command = AsyncMock()
    db_obj = MagicMock()
    client.__getitem__.return_value = db_obj

    monkeypatch.setattr(mongodb, "AsyncIOMotorClient", lambda *_: client)
    monkeypatch.setattr(mongodb, "_create_indexes", AsyncMock())

    await mongodb.connect_to_mongodb()
    assert mongodb.get_database() is db_obj
    assert mongodb.get_client() is client

    await mongodb.disconnect_from_mongodb()
    client.close.assert_called_once()


@pytest.mark.asyncio
async def test_connect_error(monkeypatch: pytest.MonkeyPatch):
    bad = MagicMock()
    bad.admin.command = AsyncMock(side_effect=RuntimeError("ping failed"))
    bad.__getitem__.return_value = MagicMock()
    monkeypatch.setattr(mongodb, "AsyncIOMotorClient", lambda *_: bad)

    with pytest.raises(RuntimeError):
        await mongodb.connect_to_mongodb()


def test_get_database_client_errors(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(mongodb, "_database", None)
    monkeypatch.setattr(mongodb, "_client", None)

    with pytest.raises(RuntimeError):
        mongodb.get_database()
    with pytest.raises(RuntimeError):
        mongodb.get_client()


@pytest.mark.asyncio
async def test_create_indexes_paths(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(mongodb, "_database", None)
    await mongodb._create_indexes()

    exercises = MagicMock()
    trainings = MagicMock()
    plans = MagicMock()
    exercises.create_index = AsyncMock()
    trainings.create_index = AsyncMock()
    plans.create_index = AsyncMock()

    fake_db = {
        mongodb.settings.EXERCISES_COLLECTION: exercises,
        mongodb.settings.TRAININGS_COLLECTION: trainings,
        mongodb.settings.WORKOUT_PLANS_COLLECTION: plans,
    }
    monkeypatch.setattr(mongodb, "_database", fake_db)
    await mongodb._create_indexes()

    assert exercises.create_index.await_count > 0
    assert trainings.create_index.await_count > 0
    assert plans.create_index.await_count > 0


@pytest.mark.asyncio
async def test_get_session(monkeypatch: pytest.MonkeyPatch):
    session_obj = object()

    class SessionCM:
        async def __aenter__(self):
            return session_obj

        async def __aexit__(self, exc_type, exc, tb):
            return False

    client = MagicMock()
    client.start_session = AsyncMock(return_value=SessionCM())
    monkeypatch.setattr(mongodb, "get_client", lambda: client)

    async with mongodb.get_session() as session:
        assert session is session_obj
