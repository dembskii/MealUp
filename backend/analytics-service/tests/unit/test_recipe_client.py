from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.services import recipe_client


class _Response:
    def __init__(self, status_code: int, payload=None, text: str = ""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload


@pytest.mark.asyncio
async def test_get_client_creates_and_reuses_client():
    recipe_client._client = None

    fake_client = MagicMock()
    fake_client.is_closed = False

    with patch("src.services.recipe_client.httpx.AsyncClient", return_value=fake_client) as mock_client_ctor:
        first = recipe_client._get_client()
        second = recipe_client._get_client()

    assert first is fake_client
    assert second is fake_client
    mock_client_ctor.assert_called_once()


@pytest.mark.asyncio
async def test_get_client_recreates_when_closed():
    recipe_client._client = SimpleNamespace(is_closed=True)
    new_client = MagicMock()
    new_client.is_closed = False

    with patch("src.services.recipe_client.httpx.AsyncClient", return_value=new_client) as mock_client_ctor:
        client = recipe_client._get_client()

    assert client is new_client
    mock_client_ctor.assert_called_once()


def test_internal_headers_uses_internal_token():
    with patch("src.services.recipe_client.settings.INTERNAL_SERVICE_TOKEN", "test-token"):
        headers = recipe_client._internal_headers()

    assert headers == {"X-Internal-Token": "test-token"}


@pytest.mark.asyncio
async def test_close_client_handles_open_and_none_state():
    closable = MagicMock()
    closable.is_closed = False
    closable.aclose = AsyncMock()
    recipe_client._client = closable

    await recipe_client.close_client()

    closable.aclose.assert_awaited_once()
    assert recipe_client._client is None

    # Should not fail when client already missing
    recipe_client._client = None
    await recipe_client.close_client()


@pytest.mark.asyncio
async def test_fetch_recipe_success_and_non_200():
    client = MagicMock()
    client.get = AsyncMock(side_effect=[_Response(200, {"id": "r1"}), _Response(404, text="missing")])

    with patch("src.services.recipe_client._get_client", return_value=client):
        ok = await recipe_client.fetch_recipe("r1")
        missing = await recipe_client.fetch_recipe("r2")

    assert ok == {"id": "r1"}
    assert missing is None


@pytest.mark.asyncio
async def test_fetch_recipe_handles_http_error():
    client = MagicMock()
    client.get = AsyncMock(side_effect=httpx.HTTPError("network"))

    with patch("src.services.recipe_client._get_client", return_value=client):
        result = await recipe_client.fetch_recipe("r1")

    assert result is None


@pytest.mark.asyncio
async def test_fetch_ingredient_success_and_error_paths():
    client = MagicMock()
    client.get = AsyncMock(
        side_effect=[
            _Response(200, {"id": "i1"}),
            _Response(500, text="boom"),
            httpx.HTTPError("down"),
        ]
    )

    with patch("src.services.recipe_client._get_client", return_value=client):
        ok = await recipe_client.fetch_ingredient("i1")
        fail = await recipe_client.fetch_ingredient("i2")
        err = await recipe_client.fetch_ingredient("i3")

    assert ok == {"id": "i1"}
    assert fail is None
    assert err is None


@pytest.mark.asyncio
async def test_fetch_ingredients_bulk_deduplicates_ids_and_filters_none():
    async def _fake_fetch(iid: str):
        return {"id": iid} if iid != "missing" else None

    with patch("src.services.recipe_client.fetch_ingredient", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.side_effect = _fake_fetch
        result = await recipe_client.fetch_ingredients_bulk(["a", "a", "missing", "b"])

    assert set(result.keys()) == {"a", "b"}
    assert mock_fetch.await_count == 3


def test_convert_to_grams_known_and_unknown_units():
    assert recipe_client.convert_to_grams(2, "kg") == 2000.0
    assert recipe_client.convert_to_grams(3, "unknown") == 3.0
