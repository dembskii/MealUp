from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.db import mongodb


@pytest.mark.asyncio
async def test_connect_to_mongodb_success_sets_client_and_db():
    admin = SimpleNamespace(command=AsyncMock())

    fake_db = MagicMock()

    class FakeClient:
        def __init__(self, *_args, **_kwargs):
            self.admin = admin

        def __getitem__(self, _name):
            return fake_db

    with patch("src.db.mongodb.AsyncIOMotorClient", FakeClient), patch(
        "src.db.mongodb._create_indexes", new_callable=AsyncMock
    ) as mock_indexes:
        await mongodb.connect_to_mongodb()

    assert mongodb._database is fake_db
    assert mongodb._client is not None
    admin.command.assert_awaited_once_with("ping")
    mock_indexes.assert_awaited_once()


@pytest.mark.asyncio
async def test_connect_to_mongodb_raises_when_client_fails():
    class FailingClient:
        def __init__(self, *_args, **_kwargs):
            raise RuntimeError("cannot connect")

    with patch("src.db.mongodb.AsyncIOMotorClient", FailingClient):
        with pytest.raises(RuntimeError, match="cannot connect"):
            await mongodb.connect_to_mongodb()


@pytest.mark.asyncio
async def test_disconnect_from_mongodb_closes_client():
    fake_client = MagicMock()
    mongodb._client = fake_client

    await mongodb.disconnect_from_mongodb()

    fake_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_create_indexes_no_database_returns_early():
    mongodb._database = None

    await mongodb._create_indexes()


@pytest.mark.asyncio
async def test_create_indexes_success_creates_expected_indexes():
    daily_logs = MagicMock()
    daily_logs.create_index = AsyncMock()

    meal_entries = MagicMock()
    meal_entries.create_index = AsyncMock()

    class FakeDB(dict):
        def __getitem__(self, key):
            return super().__getitem__(key)

    mongodb._database = FakeDB({"daily_logs": daily_logs, "meal_entries": meal_entries})

    with patch("src.db.mongodb.settings.DAILY_LOG_COLLECTION", "daily_logs"), patch(
        "src.db.mongodb.settings.MEAL_ENTRIES_COLLECTION", "meal_entries"
    ):
        await mongodb._create_indexes()

    assert daily_logs.create_index.await_count == 4
    assert meal_entries.create_index.await_count == 4


@pytest.mark.asyncio
async def test_create_indexes_handles_exceptions():
    broken_collection = MagicMock()
    broken_collection.create_index = AsyncMock(side_effect=RuntimeError("index err"))

    class FakeDB(dict):
        def __getitem__(self, key):
            return super().__getitem__(key)

    mongodb._database = FakeDB({"daily_logs": broken_collection, "meal_entries": broken_collection})

    with patch("src.db.mongodb.settings.DAILY_LOG_COLLECTION", "daily_logs"), patch(
        "src.db.mongodb.settings.MEAL_ENTRIES_COLLECTION", "meal_entries"
    ):
        await mongodb._create_indexes()


def test_get_database_and_get_client_guard_clauses_and_success():
    mongodb._database = None
    mongodb._client = None

    with pytest.raises(RuntimeError, match="Database not connected"):
        mongodb.get_database()

    with pytest.raises(RuntimeError, match="Client not connected"):
        mongodb.get_client()

    mongodb._database = MagicMock()
    mongodb._client = MagicMock()

    assert mongodb.get_database() is mongodb._database
    assert mongodb.get_client() is mongodb._client
