from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.db import mongodb
from src.services import image_generation_service


class _AsyncSessionContext:
    async def __aenter__(self):
        return "session-token"

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeClient:
    def __init__(self, db_map=None):
        self.admin = SimpleNamespace(command=AsyncMock())
        self._db_map = db_map or {}
        self.close = MagicMock()
        self.start_session = AsyncMock(return_value=_AsyncSessionContext())

    def __getitem__(self, db_name):
        return self._db_map[db_name]


@pytest.mark.asyncio
async def test_connect_and_disconnect_to_mongodb_success():
    recipes = MagicMock()
    ingredients = MagicMock()
    versions = MagicMock()
    recipes.create_index = AsyncMock()
    ingredients.create_index = AsyncMock()
    versions.create_index = AsyncMock()

    fake_db = {
        "recipes": recipes,
        "ingredients": ingredients,
        "recipe_versions": versions,
    }
    fake_client = _FakeClient(db_map={"recipe_db": fake_db})

    with patch("src.db.mongodb.AsyncIOMotorClient", return_value=fake_client):
        mongodb._client = None
        mongodb._database = None
        await mongodb.connect_to_mongodb()

    assert mongodb.get_database() is fake_db
    assert mongodb.get_client() is fake_client
    fake_client.admin.command.assert_awaited_once_with("ping")

    await mongodb.disconnect_from_mongodb()
    fake_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_connect_to_mongodb_re_raises_on_error():
    fake_client = _FakeClient(db_map={"recipe_db": {}})
    fake_client.admin.command = AsyncMock(side_effect=RuntimeError("ping failed"))

    with patch("src.db.mongodb.AsyncIOMotorClient", return_value=fake_client):
        with pytest.raises(RuntimeError):
            await mongodb.connect_to_mongodb()


def test_get_database_and_client_raise_when_uninitialized():
    mongodb._client = None
    mongodb._database = None

    with pytest.raises(RuntimeError):
        mongodb.get_database()
    with pytest.raises(RuntimeError):
        mongodb.get_client()


@pytest.mark.asyncio
async def test_create_indexes_no_database_and_error_path():
    mongodb._database = None
    await mongodb._create_indexes()

    recipes = MagicMock()
    ingredients = MagicMock()
    versions = MagicMock()
    recipes.create_index = AsyncMock(side_effect=RuntimeError("index fail"))
    ingredients.create_index = AsyncMock()
    versions.create_index = AsyncMock()
    mongodb._database = {
        "recipes": recipes,
        "ingredients": ingredients,
        "recipe_versions": versions,
    }

    await mongodb._create_indexes()


@pytest.mark.asyncio
async def test_get_session_context_manager():
    fake_client = _FakeClient(db_map={})
    mongodb._client = fake_client

    async with mongodb.get_session() as session:
        assert session == "session-token"


def test_build_prompt_contains_recipe_name():
    prompt = image_generation_service._build_prompt("Ramen")
    assert "Ramen" in prompt
    assert "food photography" in prompt


@pytest.mark.asyncio
async def test_generate_recipe_image_skips_without_api_key(monkeypatch):
    monkeypatch.setattr(image_generation_service.settings, "OPEN_ROUTER_API_KEY", "")

    await image_generation_service.generate_recipe_image("recipe-1", "Soup")


@pytest.mark.asyncio
async def test_generate_recipe_image_success(monkeypatch):
    monkeypatch.setattr(image_generation_service.settings, "OPEN_ROUTER_API_KEY", "test-key")

    mock_collection = MagicMock()
    mock_collection.update_one = AsyncMock()
    mock_db = {"recipes": mock_collection}

    fake_response = MagicMock()
    fake_response.raise_for_status = MagicMock()
    fake_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "images": [{"image_url": {"url": "data:image/png;base64,abc"}}]
                }
            }
        ]
    }

    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=fake_response)
    mock_client_ctx = MagicMock()
    mock_client_ctx.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch("src.services.image_generation_service.get_database", return_value=mock_db), patch(
        "src.services.image_generation_service.httpx.AsyncClient", return_value=mock_client_ctx
    ):
        await image_generation_service.generate_recipe_image("recipe-1", "Soup")

    mock_collection.update_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_recipe_image_handles_empty_and_keyerror_and_http_error(monkeypatch):
    monkeypatch.setattr(image_generation_service.settings, "OPEN_ROUTER_API_KEY", "test-key")

    empty_url_response = MagicMock()
    empty_url_response.raise_for_status = MagicMock()
    empty_url_response.json.return_value = {
        "choices": [{"message": {"images": [{"image_url": {"url": ""}}]}}]
    }

    key_error_response = MagicMock()
    key_error_response.raise_for_status = MagicMock()
    key_error_response.json.return_value = {"choices": []}

    request = httpx.Request("POST", "https://example.com")
    response = httpx.Response(status_code=500, request=request)
    http_error_response = MagicMock()
    http_error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "error", request=request, response=response
    )

    for fake_response in (empty_url_response, key_error_response, http_error_response):
        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=fake_response)
        mock_client_ctx = MagicMock()
        mock_client_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("src.services.image_generation_service.httpx.AsyncClient", return_value=mock_client_ctx), patch(
            "src.services.image_generation_service.get_database", return_value={"recipes": MagicMock()}
        ):
            await image_generation_service.generate_recipe_image("recipe-1", "Soup")


@pytest.mark.asyncio
async def test_generate_recipe_image_handles_generic_exception(monkeypatch):
    monkeypatch.setattr(image_generation_service.settings, "OPEN_ROUTER_API_KEY", "test-key")

    mock_client = MagicMock()
    mock_client.post = AsyncMock(side_effect=RuntimeError("network fail"))
    mock_client_ctx = MagicMock()
    mock_client_ctx.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch("src.services.image_generation_service.httpx.AsyncClient", return_value=mock_client_ctx):
        await image_generation_service.generate_recipe_image("recipe-1", "Soup")
