from unittest.mock import AsyncMock, MagicMock

import pytest

import src.init_exercises as seed


def test_module_loaded_and_id_deterministic():
    assert len(seed.ALL_EXERCISES) > 100
    assert seed.make_exercise_id("Push Up") == seed.make_exercise_id(" push up ")


def test_build_exercise():
    exercise = seed.build_exercise(
        "X",
        seed.BP.CHEST,
        seed.ADV.BEGINNER,
        seed.CAT.STRENGTH,
        "desc",
        ["hint"],
    )
    assert exercise.name == "X"
    assert exercise.body_part == seed.BP.CHEST


@pytest.mark.asyncio
async def test_init_exercises_skip_when_exists(monkeypatch: pytest.MonkeyPatch):
    collection = MagicMock()
    collection.count_documents = AsyncMock(return_value=5)

    monkeypatch.setattr(seed, "connect_to_mongodb", AsyncMock())
    monkeypatch.setattr(seed, "disconnect_from_mongodb", AsyncMock())
    monkeypatch.setattr(seed, "get_database", lambda: {seed.settings.EXERCISES_COLLECTION: collection})

    await seed.init_exercises()

    seed.disconnect_from_mongodb.assert_awaited_once()


@pytest.mark.asyncio
async def test_init_exercises_insert(monkeypatch: pytest.MonkeyPatch):
    collection = MagicMock()
    collection.count_documents = AsyncMock(return_value=0)
    insert_result = MagicMock()
    insert_result.inserted_ids = [1, 2]
    collection.insert_many = AsyncMock(return_value=insert_result)

    monkeypatch.setattr(seed, "connect_to_mongodb", AsyncMock())
    monkeypatch.setattr(seed, "disconnect_from_mongodb", AsyncMock())
    monkeypatch.setattr(seed, "get_database", lambda: {seed.settings.EXERCISES_COLLECTION: collection})

    await seed.init_exercises()

    assert collection.insert_many.await_count == 1


@pytest.mark.asyncio
async def test_init_exercises_exception_still_disconnects(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(seed, "connect_to_mongodb", AsyncMock(side_effect=RuntimeError("no db")))
    monkeypatch.setattr(seed, "disconnect_from_mongodb", AsyncMock())

    with pytest.raises(RuntimeError):
        await seed.init_exercises()

    seed.disconnect_from_mongodb.assert_awaited_once()
