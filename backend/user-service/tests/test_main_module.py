from fastapi import FastAPI

import pytest

import src.main as main_module


@pytest.mark.asyncio
async def test_lifespan_runs():
    async with main_module.lifespan(FastAPI()):
        pass


def test_root_and_health(client):
    root = client.get("/")
    assert root.status_code == 200
    assert root.json()["message"] == "User Service is running"

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["service"] == "user-service"
