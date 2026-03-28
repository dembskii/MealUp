from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import src.main as main_module


@pytest.mark.asyncio
async def test_lifespan_calls_connect_disconnect(monkeypatch: pytest.MonkeyPatch):
    connect = AsyncMock()
    disconnect = AsyncMock()
    monkeypatch.setattr(main_module, "connect_to_mongodb", connect)
    monkeypatch.setattr(main_module, "disconnect_from_mongodb", disconnect)

    async with main_module.lifespan(FastAPI()):
        pass

    connect.assert_awaited_once()
    disconnect.assert_awaited_once()


def test_root_and_health(client):
    assert client.get("/").status_code == 200
    assert client.get("/health").status_code == 200
