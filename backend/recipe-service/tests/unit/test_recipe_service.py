from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models.model import CapacityUnit, IngredientCreate, IngredientUpdate, RecipeCreate, RecipeUpdate
from src.services.recipe_service import IngredientService, RecipeService


def _ingredient_doc(ingredient_id: str = "ing-1", name: str = "Tomato") -> dict:
    from src.models.model import Ingredient

    return Ingredient(_id=ingredient_id, name=name, units="g").model_dump(by_alias=True)


def _recipe_doc(recipe_id: str = "rec-1", author_id: str = "author-1", likes: int = 0) -> dict:
    from src.models.model import Recipe, WeightedIngredient

    return Recipe(
        _id=recipe_id,
        name="Pasta",
        author_id=author_id,
        ingredients=[
            WeightedIngredient(
                ingredient_id="ing-1",
                capacity=CapacityUnit.GRAM,
                quantity=100,
            )
        ],
        prepare_instruction=["step"],
        time_to_prepare=120,
        total_likes=likes,
    ).model_dump(by_alias=True)


@pytest.mark.asyncio
async def test_ingredient_create():
    collection = MagicMock()
    collection.insert_one = AsyncMock()
    db = {"ingredients": collection}

    with patch("src.services.recipe_service.get_database", return_value=db):
        created = await IngredientService.create_ingredient(IngredientCreate(name="Salt", units="g"))

    assert created.name == "Salt"
    collection.insert_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_ingredient_get_found_and_missing():
    collection = MagicMock()
    collection.find_one = AsyncMock(side_effect=[_ingredient_doc(), None])
    db = {"ingredients": collection}

    with patch("src.services.recipe_service.get_database", return_value=db):
        found = await IngredientService.get_ingredient("ing-1")
        missing = await IngredientService.get_ingredient("missing")

    assert found is not None
    assert found.id == "ing-1"
    assert missing is None


@pytest.mark.asyncio
async def test_get_ingredients_with_and_without_search():
    cursor = MagicMock()
    cursor.sort.return_value = cursor
    cursor.skip.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.to_list = AsyncMock(return_value=[_ingredient_doc("ing-1"), _ingredient_doc("ing-2", "Pepper")])

    collection = MagicMock()
    collection.find.return_value = cursor
    db = {"ingredients": collection}

    with patch("src.services.recipe_service.get_database", return_value=db):
        result = await IngredientService.get_ingredients(skip=1, limit=2, search="pep")

    assert len(result) == 2
    collection.find.assert_called_once_with({"name": {"$regex": "pep", "$options": "i"}})


@pytest.mark.asyncio
async def test_update_ingredient_not_found():
    collection = MagicMock()
    collection.find_one = AsyncMock(return_value=None)
    db = {"ingredients": collection}

    with patch("src.services.recipe_service.get_database", return_value=db):
        result = await IngredientService.update_ingredient("missing", IngredientUpdate(name="New"))

    assert result is None


@pytest.mark.asyncio
async def test_update_ingredient_without_payload_changes_returns_existing():
    existing = _ingredient_doc("ing-10", "Milk")
    collection = MagicMock()
    collection.find_one = AsyncMock(return_value=existing)
    db = {"ingredients": collection}

    with patch("src.services.recipe_service.get_database", return_value=db):
        result = await IngredientService.update_ingredient("ing-10", IngredientUpdate())

    assert result is not None
    assert result.name == "Milk"


@pytest.mark.asyncio
async def test_update_ingredient_with_payload_handles_updated_lookup():
    existing = _ingredient_doc("ing-11", "Oil")
    updated = _ingredient_doc("ing-11", "Olive Oil")

    collection = MagicMock()
    collection.find_one = AsyncMock(side_effect=[existing, updated, None])
    collection.update_one = AsyncMock()
    db = {"ingredients": collection}

    with patch("src.services.recipe_service.get_database", return_value=db):
        ok = await IngredientService.update_ingredient("ing-11", IngredientUpdate(name="Olive Oil"))

    assert ok is not None
    assert ok.name == "Olive Oil"

    collection.find_one = AsyncMock(side_effect=[existing, None])
    with patch("src.services.recipe_service.get_database", return_value=db):
        none_after_update = await IngredientService.update_ingredient("ing-11", IngredientUpdate(name="Olive Oil"))
    assert none_after_update is None


@pytest.mark.asyncio
async def test_delete_ingredient_true_and_false():
    collection = MagicMock()
    collection.delete_one = AsyncMock(side_effect=[SimpleNamespace(deleted_count=1), SimpleNamespace(deleted_count=0)])
    db = {"ingredients": collection}

    with patch("src.services.recipe_service.get_database", return_value=db):
        ok = await IngredientService.delete_ingredient("ing-1")
        fail = await IngredientService.delete_ingredient("ing-1")

    assert ok is True
    assert fail is False


@pytest.mark.asyncio
async def test_recipe_create_and_get_paths():
    collection = MagicMock()
    collection.insert_one = AsyncMock()
    collection.find_one = AsyncMock(side_effect=[_recipe_doc("rec-1"), None])
    db = {"recipes": collection}

    recipe_create = RecipeCreate(
        name="Pasta",
        ingredients=[{"ingredient_id": "ing-1", "capacity": "g", "quantity": 100}],
        prepare_instruction=["step"],
        time_to_prepare=120,
    )

    with patch("src.services.recipe_service.get_database", return_value=db):
        created = await RecipeService.create_recipe(recipe_create, "author-1")
        found = await RecipeService.get_recipe("rec-1")
        missing = await RecipeService.get_recipe("missing")

    assert created.author_id == "author-1"
    assert found is not None
    assert missing is None


@pytest.mark.asyncio
async def test_get_recipes_filter_and_mapping():
    cursor = MagicMock()
    cursor.sort.return_value = cursor
    cursor.skip.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.to_list = AsyncMock(return_value=[_recipe_doc("r1", "a1"), _recipe_doc("r2", "a1")])

    collection = MagicMock()
    collection.find.return_value = cursor
    db = {"recipes": collection}

    with patch("src.services.recipe_service.get_database", return_value=db):
        result = await RecipeService.get_recipes(skip=0, limit=2, author_id="a1")

    assert len(result) == 2
    collection.find.assert_called_once_with({"author_id": "a1"})


@pytest.mark.asyncio
async def test_update_recipe_branches():
    collection = MagicMock()
    db = {"recipes": collection}

    collection.find_one = AsyncMock(return_value=None)
    with patch("src.services.recipe_service.get_database", return_value=db):
        not_found = await RecipeService.update_recipe("rec-1", RecipeUpdate(time_to_prepare=300), "author-1")
    assert not_found is None

    existing = _recipe_doc("rec-1", "author-1")
    collection.find_one = AsyncMock(return_value=existing)
    with patch("src.services.recipe_service.get_database", return_value=db):
        unchanged = await RecipeService.update_recipe("rec-1", RecipeUpdate(), "author-1")
    assert unchanged is not None
    assert unchanged.id == "rec-1"

    collection.find_one = AsyncMock(side_effect=[existing, _recipe_doc("rec-1", "author-1")])
    collection.update_one = AsyncMock(return_value=SimpleNamespace(modified_count=1))
    with patch("src.services.recipe_service.get_database", return_value=db):
        updated = await RecipeService.update_recipe("rec-1", RecipeUpdate(time_to_prepare=350), "author-1")
    assert updated is not None

    collection.find_one = AsyncMock(return_value=existing)
    collection.update_one = AsyncMock(return_value=SimpleNamespace(modified_count=0))
    with patch("src.services.recipe_service.get_database", return_value=db):
        fallback = await RecipeService.update_recipe("rec-1", RecipeUpdate(time_to_prepare=350), "author-1")
    assert fallback is not None

    collection.find_one = AsyncMock(side_effect=[existing, None])
    collection.update_one = AsyncMock(return_value=SimpleNamespace(modified_count=1))
    with patch("src.services.recipe_service.get_database", return_value=db):
        missing_after_update = await RecipeService.update_recipe("rec-1", RecipeUpdate(time_to_prepare=350), "author-1")
    assert missing_after_update is None


@pytest.mark.asyncio
async def test_delete_recipe_true_and_false():
    collection = MagicMock()
    collection.delete_one = AsyncMock(side_effect=[SimpleNamespace(deleted_count=1), SimpleNamespace(deleted_count=0)])
    db = {"recipes": collection}

    with patch("src.services.recipe_service.get_database", return_value=db):
        ok = await RecipeService.delete_recipe("rec-1", "author-1")
        fail = await RecipeService.delete_recipe("rec-1", "author-1")

    assert ok is True
    assert fail is False


@pytest.mark.asyncio
async def test_like_and_unlike_recipe_branches():
    collection = MagicMock()
    db = {"recipes": collection}

    collection.update_one = AsyncMock(return_value=SimpleNamespace(modified_count=0))
    with patch("src.services.recipe_service.get_database", return_value=db):
        no_like = await RecipeService.like_recipe("rec-1")
    assert no_like is None

    collection.update_one = AsyncMock(return_value=SimpleNamespace(modified_count=1))
    collection.find_one = AsyncMock(return_value=_recipe_doc("rec-1", likes=1))
    with patch("src.services.recipe_service.get_database", return_value=db):
        liked = await RecipeService.like_recipe("rec-1")
    assert liked is not None
    assert liked.total_likes == 1

    collection.find_one = AsyncMock(return_value=None)
    with patch("src.services.recipe_service.get_database", return_value=db):
        liked_missing = await RecipeService.like_recipe("rec-1")
    assert liked_missing is None

    collection.update_one = AsyncMock(return_value=SimpleNamespace(modified_count=0))
    with patch("src.services.recipe_service.get_database", return_value=db):
        no_unlike = await RecipeService.unlike_recipe("rec-1")
    assert no_unlike is None

    collection.update_one = AsyncMock(return_value=SimpleNamespace(modified_count=1))
    collection.find_one = AsyncMock(return_value=_recipe_doc("rec-1", likes=0))
    with patch("src.services.recipe_service.get_database", return_value=db):
        unliked = await RecipeService.unlike_recipe("rec-1")
    assert unliked is not None

    collection.find_one = AsyncMock(return_value=None)
    with patch("src.services.recipe_service.get_database", return_value=db):
        unliked_missing = await RecipeService.unlike_recipe("rec-1")
    assert unliked_missing is None


@pytest.mark.asyncio
async def test_search_recipes_builds_filters():
    cursor = MagicMock()
    cursor.sort.return_value = cursor
    cursor.skip.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.to_list = AsyncMock(return_value=[_recipe_doc("r1", "author-x")])

    collection = MagicMock()
    collection.find.return_value = cursor
    db = {"recipes": collection}

    with patch("src.services.recipe_service.get_database", return_value=db):
        result = await RecipeService.search_recipes(
            query="pasta",
            tags=["quick"],
            author_id="author-x",
            skip=2,
            limit=5,
        )

    assert len(result) == 1
    collection.find.assert_called_once_with(
        {
            "$or": [
                {"name": {"$regex": "pasta", "$options": "i"}},
                {"prepare_instruction": {"$regex": "pasta", "$options": "i"}},
            ],
            "tags": {"$in": ["quick"]},
            "author_id": "author-x",
        }
    )
