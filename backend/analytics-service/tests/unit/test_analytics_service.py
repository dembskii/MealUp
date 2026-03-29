from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models.daily_log import DailyLog
from src.models.meal_entry import MacroNutrients, MealEntry, MealIngredient, MealType
from src.services.analytics_service import (
    DailyLogService,
    MealEntryService,
    _compute_macros_for_quantity,
    _compute_meal_macros,
    _resolve_ingredients_from_recipe,
    _resolve_manual_ingredients,
)
from src.validators.daily_log import DailyGoalsUpdate
from src.validators.meal_entry import MealEntryCreate, MealEntryUpdate, MealIngredientCreate


def _daily_log_doc(user_id: str = "user-1", date: str = "2026-03-20") -> dict:
    return DailyLog(
        user_id=user_id,
        date=date,
        total_macros=MacroNutrients(calories=100.0, proteins=10.0, carbs=20.0, fats=3.0),
        calorie_goal=2000.0,
    ).model_dump(by_alias=True)


def _meal_doc(entry_id: str = "entry-1", user_id: str = "user-1", date: str = "2026-03-20") -> dict:
    return MealEntry(
        _id=entry_id,
        user_id=user_id,
        daily_log_id="log-1",
        date=date,
        meal_type=MealType.LUNCH,
        ingredients=[
            MealIngredient(
                ingredient_id="ing-1",
                name="Chicken",
                quantity=100.0,
                macros=MacroNutrients(calories=200.0, proteins=30.0, carbs=0.0, fats=5.0),
            )
        ],
        total_macros=MacroNutrients(calories=200.0, proteins=30.0, carbs=0.0, fats=5.0),
        note="Meal",
    ).model_dump(by_alias=True)


def test_compute_macros_for_quantity_scales_values():
    result = _compute_macros_for_quantity(
        {"calories": 100, "proteins": 10, "carbs": 20, "fats": 5},
        250.0,
    )

    assert result.calories == 250.0
    assert result.proteins == 25.0
    assert result.carbs == 50.0
    assert result.fats == 12.5


def test_compute_meal_macros_sums_model_and_object_variants():
    item_model = MealIngredient(
        ingredient_id="ing-1",
        name="A",
        quantity=50.0,
        macros=MacroNutrients(calories=120.5, proteins=11.1, carbs=2.2, fats=3.3),
    )
    item_other = SimpleNamespace(macros=MacroNutrients(calories=79.5, proteins=8.9, carbs=1.8, fats=1.7))

    total = _compute_meal_macros([item_model, item_other])

    assert total.model_dump() == {
        "calories": 200.0,
        "proteins": 20.0,
        "carbs": 4.0,
        "fats": 5.0,
    }


@pytest.mark.asyncio
@patch("src.services.analytics_service.convert_to_grams")
@patch("src.services.analytics_service.fetch_ingredients_bulk", new_callable=AsyncMock)
@patch("src.services.analytics_service.fetch_recipe", new_callable=AsyncMock)
async def test_resolve_ingredients_from_recipe_success(mock_fetch_recipe, mock_fetch_bulk, mock_convert):
    mock_fetch_recipe.return_value = {
        "name": "Recipe X",
        "ingredients": [{"ingredient_id": "ing-1", "quantity": 2, "capacity": "kg"}],
    }
    mock_fetch_bulk.return_value = {
        "ing-1": {
            "name": "Rice",
            "macro_per_hundred": {"calories": 100, "proteins": 2, "carbs": 22, "fats": 0.5},
        }
    }
    mock_convert.return_value = 500.0

    ingredients, recipe_name = await _resolve_ingredients_from_recipe("recipe-1")

    assert recipe_name == "Recipe X"
    assert len(ingredients) == 1
    assert ingredients[0].ingredient_id == "ing-1"
    assert ingredients[0].quantity == 500.0
    assert ingredients[0].macros.calories == 500.0


@pytest.mark.asyncio
@patch("src.services.analytics_service.fetch_recipe", new_callable=AsyncMock)
async def test_resolve_ingredients_from_recipe_not_found(mock_fetch_recipe):
    mock_fetch_recipe.return_value = None

    with pytest.raises(ValueError, match="not found"):
        await _resolve_ingredients_from_recipe("missing")


@pytest.mark.asyncio
@patch("src.services.analytics_service.fetch_recipe", new_callable=AsyncMock)
async def test_resolve_ingredients_from_recipe_without_ingredients(mock_fetch_recipe):
    mock_fetch_recipe.return_value = {"name": "Empty", "ingredients": []}

    with pytest.raises(ValueError, match="has no ingredients"):
        await _resolve_ingredients_from_recipe("recipe-empty")


@pytest.mark.asyncio
@patch("src.services.analytics_service.convert_to_grams")
@patch("src.services.analytics_service.fetch_ingredients_bulk", new_callable=AsyncMock)
@patch("src.services.analytics_service.fetch_recipe", new_callable=AsyncMock)
async def test_resolve_ingredients_from_recipe_skips_missing_and_handles_no_macros(
    mock_fetch_recipe,
    mock_fetch_bulk,
    mock_convert,
):
    mock_fetch_recipe.return_value = {
        "name": "Recipe Y",
        "ingredients": [
            {"ingredient_id": "ing-missing", "quantity": 1, "capacity": "g"},
            {"ingredient_id": "ing-no-macros", "quantity": 2, "capacity": "g"},
        ],
    }
    mock_fetch_bulk.return_value = {
        "ing-no-macros": {
            "name": "Unknown Macro Ingredient",
            "macro_per_hundred": None,
        }
    }
    mock_convert.side_effect = [1.0, 2.0]

    ingredients, _ = await _resolve_ingredients_from_recipe("recipe-y")

    assert len(ingredients) == 1
    assert ingredients[0].ingredient_id == "ing-no-macros"
    assert ingredients[0].macros.model_dump() == {
        "calories": 0.0,
        "proteins": 0.0,
        "carbs": 0.0,
        "fats": 0.0,
    }


@pytest.mark.asyncio
@patch("src.services.analytics_service.fetch_ingredients_bulk", new_callable=AsyncMock)
async def test_resolve_manual_ingredients_trust_mode_and_resolve_mode(mock_fetch_bulk):
    trusted_macros = MacroNutrients(calories=50.0, proteins=1.0, carbs=10.0, fats=0.2)
    raw = [
        MealIngredientCreate(
            ingredient_id="trusted",
            name="Banana",
            quantity=100.0,
            macros=trusted_macros,
        ),
        MealIngredientCreate(
            ingredient_id="resolved",
            quantity=40.0,
        ),
    ]
    mock_fetch_bulk.return_value = {
        "resolved": {
            "name": "Oats",
            "macro_per_hundred": {"calories": 300, "proteins": 10, "carbs": 60, "fats": 5},
        }
    }

    resolved = await _resolve_manual_ingredients(raw)

    assert len(resolved) == 2
    assert resolved[0].ingredient_id == "trusted"
    assert resolved[0].macros.calories == 50.0
    assert resolved[1].name == "Oats"
    assert resolved[1].macros.calories == 120.0


@pytest.mark.asyncio
@patch("src.services.analytics_service.fetch_ingredients_bulk", new_callable=AsyncMock)
async def test_resolve_manual_ingredients_skips_missing(mock_fetch_bulk):
    raw = [MealIngredientCreate(ingredient_id="missing", quantity=20.0)]
    mock_fetch_bulk.return_value = {}

    resolved = await _resolve_manual_ingredients(raw)

    assert resolved == []


@pytest.mark.asyncio
@patch("src.services.analytics_service.fetch_ingredients_bulk", new_callable=AsyncMock)
async def test_resolve_manual_ingredients_uses_default_macros_when_missing(mock_fetch_bulk):
    raw = [MealIngredientCreate(ingredient_id="ing-1", quantity=20.0)]
    mock_fetch_bulk.return_value = {"ing-1": {"name": "Oil", "macro_per_hundred": None}}

    resolved = await _resolve_manual_ingredients(raw)

    assert len(resolved) == 1
    assert resolved[0].macros.calories == 0.0


@pytest.mark.asyncio
async def test_daily_log_service_get_or_create_returns_existing():
    collection = MagicMock()
    collection.find_one = AsyncMock(return_value=_daily_log_doc())
    db = {"daily_logs": collection}

    with patch("src.services.analytics_service.get_database", return_value=db):
        log = await DailyLogService.get_or_create_daily_log("user-1", "2026-03-20")

    assert isinstance(log, DailyLog)
    collection.insert_one.assert_not_called()


@pytest.mark.asyncio
async def test_daily_log_service_get_or_create_creates_new():
    collection = MagicMock()
    collection.find_one = AsyncMock(return_value=None)
    collection.insert_one = AsyncMock()
    db = {"daily_logs": collection}

    with patch("src.services.analytics_service.get_database", return_value=db):
        log = await DailyLogService.get_or_create_daily_log("user-1", "2026-03-20")

    assert isinstance(log, DailyLog)
    collection.insert_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_daily_log_service_get_daily_log_found_and_missing():
    collection = MagicMock()
    collection.find_one = AsyncMock(side_effect=[_daily_log_doc(), None])
    db = {"daily_logs": collection}

    with patch("src.services.analytics_service.get_database", return_value=db):
        found = await DailyLogService.get_daily_log("user-1", "2026-03-20")
        missing = await DailyLogService.get_daily_log("user-1", "2026-03-21")

    assert isinstance(found, DailyLog)
    assert missing is None


@pytest.mark.asyncio
async def test_daily_log_service_get_daily_logs_range():
    cursor = MagicMock()
    cursor.sort.return_value = cursor
    cursor.to_list = AsyncMock(return_value=[_daily_log_doc(date="2026-03-20")])

    collection = MagicMock()
    collection.find.return_value = cursor
    db = {"daily_logs": collection}

    with patch("src.services.analytics_service.get_database", return_value=db):
        logs = await DailyLogService.get_daily_logs_range("user-1", "2026-03-19", "2026-03-21")

    assert len(logs) == 1
    assert isinstance(logs[0], DailyLog)
    collection.find.assert_called_once()


@pytest.mark.asyncio
async def test_daily_log_service_update_goals_updates_values():
    collection = MagicMock()
    collection.update_one = AsyncMock()
    collection.find_one = AsyncMock(return_value=_daily_log_doc())
    db = {"daily_logs": collection}

    with patch("src.services.analytics_service.get_database", return_value=db), patch(
        "src.services.analytics_service.DailyLogService.get_or_create_daily_log",
        new_callable=AsyncMock,
    ) as mock_ensure:
        updated = await DailyLogService.update_goals(
            "user-1",
            "2026-03-20",
            DailyGoalsUpdate(calorie_goal=2200.0),
        )

    assert isinstance(updated, DailyLog)
    mock_ensure.assert_awaited_once_with("user-1", "2026-03-20")
    collection.update_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_daily_log_service_update_goals_without_fields_returns_log():
    collection = MagicMock()
    collection.update_one = AsyncMock()
    collection.find_one = AsyncMock(return_value=_daily_log_doc())
    db = {"daily_logs": collection}

    with patch("src.services.analytics_service.get_database", return_value=db), patch(
        "src.services.analytics_service.DailyLogService.get_or_create_daily_log",
        new_callable=AsyncMock,
    ):
        updated = await DailyLogService.update_goals("user-1", "2026-03-20", DailyGoalsUpdate())

    assert isinstance(updated, DailyLog)
    collection.update_one.assert_not_called()


@pytest.mark.asyncio
async def test_daily_log_service_recalculate_daily_totals_updates_aggregate():
    meals_cursor = MagicMock()
    meals_cursor.to_list = AsyncMock(
        return_value=[
            {"total_macros": {"calories": 100.0, "proteins": 10.0, "carbs": 20.0, "fats": 3.0}},
            {"total_macros": {"calories": 150.0, "proteins": 12.0, "carbs": 30.0, "fats": 5.0}},
        ]
    )

    daily_collection = MagicMock()
    daily_collection.update_one = AsyncMock()

    meals_collection = MagicMock()
    meals_collection.find.return_value = meals_cursor

    db = {"daily_logs": daily_collection, "meal_entries": meals_collection}

    with patch("src.services.analytics_service.get_database", return_value=db):
        await DailyLogService.recalculate_daily_totals("user-1", "2026-03-20")

    daily_collection.update_one.assert_awaited_once()
    update_doc = daily_collection.update_one.await_args.args[1]["$set"]["total_macros"]
    assert update_doc == {"calories": 250.0, "proteins": 22.0, "carbs": 50.0, "fats": 8.0}


@pytest.mark.asyncio
async def test_meal_entry_service_create_rejects_empty_payload():
    data = MealEntryCreate(date="2026-03-20", meal_type="breakfast")
    db = {"meal_entries": MagicMock()}

    with patch("src.services.analytics_service.get_database", return_value=db):
        with pytest.raises(ValueError, match="Either recipe_id or ingredients"):
            await MealEntryService.create_meal_entry(data, "user-1")


@pytest.mark.asyncio
async def test_meal_entry_service_create_recipe_mode():
    collection = MagicMock()
    collection.insert_one = AsyncMock()
    db = {"meal_entries": collection}

    resolved = [
        MealIngredient(
            ingredient_id="ing-1",
            name="Rice",
            quantity=100.0,
            macros=MacroNutrients(calories=130.0, proteins=2.0, carbs=28.0, fats=0.3),
        )
    ]

    data = MealEntryCreate(date="2026-03-20", meal_type="lunch", recipe_id="recipe-1")

    with patch("src.services.analytics_service.get_database", return_value=db), patch(
        "src.services.analytics_service.DailyLogService.get_or_create_daily_log",
        new_callable=AsyncMock,
        return_value=DailyLog(_id="log-1", user_id="user-1", date="2026-03-20"),
    ), patch(
        "src.services.analytics_service._resolve_ingredients_from_recipe",
        new_callable=AsyncMock,
        return_value=(resolved, "Recipe Name"),
    ) as mock_resolve, patch(
        "src.services.analytics_service.DailyLogService.recalculate_daily_totals",
        new_callable=AsyncMock,
    ) as mock_recalc:
        created = await MealEntryService.create_meal_entry(data, "user-1")

    assert isinstance(created, MealEntry)
    assert created.recipe_name == "Recipe Name"
    mock_resolve.assert_awaited_once_with("recipe-1")
    collection.insert_one.assert_awaited_once()
    mock_recalc.assert_awaited_once_with("user-1", "2026-03-20")


@pytest.mark.asyncio
async def test_meal_entry_service_create_manual_mode():
    collection = MagicMock()
    collection.insert_one = AsyncMock()
    db = {"meal_entries": collection}

    resolved = [
        MealIngredient(
            ingredient_id="ing-1",
            name="Banana",
            quantity=100.0,
            macros=MacroNutrients(calories=90.0, proteins=1.0, carbs=20.0, fats=0.2),
        )
    ]

    data = MealEntryCreate(
        date="2026-03-20",
        meal_type="breakfast",
        ingredients=[MealIngredientCreate(ingredient_id="ing-1", quantity=100.0)],
    )

    with patch("src.services.analytics_service.get_database", return_value=db), patch(
        "src.services.analytics_service.DailyLogService.get_or_create_daily_log",
        new_callable=AsyncMock,
        return_value=DailyLog(_id="log-1", user_id="user-1", date="2026-03-20"),
    ), patch(
        "src.services.analytics_service._resolve_manual_ingredients",
        new_callable=AsyncMock,
        return_value=resolved,
    ) as mock_resolve, patch(
        "src.services.analytics_service.DailyLogService.recalculate_daily_totals",
        new_callable=AsyncMock,
    ):
        created = await MealEntryService.create_meal_entry(data, "user-1")

    assert isinstance(created, MealEntry)
    assert created.total_macros.calories == 90.0
    mock_resolve.assert_awaited_once()


@pytest.mark.asyncio
async def test_meal_entry_service_get_meal_entry_found_and_missing():
    collection = MagicMock()
    collection.find_one = AsyncMock(side_effect=[_meal_doc(), None])
    db = {"meal_entries": collection}

    with patch("src.services.analytics_service.get_database", return_value=db):
        found = await MealEntryService.get_meal_entry("entry-1", "user-1")
        missing = await MealEntryService.get_meal_entry("entry-2", "user-1")

    assert isinstance(found, MealEntry)
    assert missing is None


@pytest.mark.asyncio
async def test_meal_entry_service_get_meals_for_date():
    cursor = MagicMock()
    cursor.sort.return_value = cursor
    cursor.to_list = AsyncMock(return_value=[_meal_doc()])

    collection = MagicMock()
    collection.find.return_value = cursor
    db = {"meal_entries": collection}

    with patch("src.services.analytics_service.get_database", return_value=db):
        meals = await MealEntryService.get_meals_for_date("user-1", "2026-03-20")

    assert len(meals) == 1
    assert isinstance(meals[0], MealEntry)


@pytest.mark.asyncio
async def test_meal_entry_service_update_returns_none_when_missing():
    collection = MagicMock()
    collection.find_one = AsyncMock(return_value=None)
    db = {"meal_entries": collection}

    with patch("src.services.analytics_service.get_database", return_value=db):
        updated = await MealEntryService.update_meal_entry(
            "entry-1",
            MealEntryUpdate(note="X"),
            "user-1",
        )

    assert updated is None


@pytest.mark.asyncio
async def test_meal_entry_service_update_recipe_branch():
    existing = _meal_doc(entry_id="entry-1")
    updated = _meal_doc(entry_id="entry-1")
    updated["recipe_name"] = "Resolved Recipe"

    collection = MagicMock()
    collection.find_one = AsyncMock(side_effect=[existing, updated])
    collection.update_one = AsyncMock()
    db = {"meal_entries": collection}

    resolved = [
        MealIngredient(
            ingredient_id="ing-1",
            name="Rice",
            quantity=100.0,
            macros=MacroNutrients(calories=130.0, proteins=2.0, carbs=28.0, fats=0.3),
        )
    ]

    with patch("src.services.analytics_service.get_database", return_value=db), patch(
        "src.services.analytics_service._resolve_ingredients_from_recipe",
        new_callable=AsyncMock,
        return_value=(resolved, "Resolved Recipe"),
    ), patch(
        "src.services.analytics_service.DailyLogService.recalculate_daily_totals",
        new_callable=AsyncMock,
    ) as mock_recalc:
        result = await MealEntryService.update_meal_entry(
            "entry-1",
            MealEntryUpdate(recipe_id="recipe-2"),
            "user-1",
        )

    assert isinstance(result, MealEntry)
    collection.update_one.assert_awaited_once()
    mock_recalc.assert_awaited_once_with("user-1", existing["date"])


@pytest.mark.asyncio
async def test_meal_entry_service_update_ingredients_branch():
    existing = _meal_doc(entry_id="entry-1")
    updated = _meal_doc(entry_id="entry-1")

    collection = MagicMock()
    collection.find_one = AsyncMock(side_effect=[existing, updated])
    collection.update_one = AsyncMock()
    db = {"meal_entries": collection}

    resolved = [
        MealIngredient(
            ingredient_id="ing-2",
            name="Oats",
            quantity=50.0,
            macros=MacroNutrients(calories=190.0, proteins=6.0, carbs=30.0, fats=3.0),
        )
    ]

    with patch("src.services.analytics_service.get_database", return_value=db), patch(
        "src.services.analytics_service._resolve_manual_ingredients",
        new_callable=AsyncMock,
        return_value=resolved,
    ), patch(
        "src.services.analytics_service.DailyLogService.recalculate_daily_totals",
        new_callable=AsyncMock,
    ):
        result = await MealEntryService.update_meal_entry(
            "entry-1",
            MealEntryUpdate(ingredients=[MealIngredientCreate(ingredient_id="ing-2", quantity=50.0)]),
            "user-1",
        )

    assert isinstance(result, MealEntry)
    collection.update_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_meal_entry_service_update_empty_updates_returns_existing():
    existing = _meal_doc(entry_id="entry-1")

    collection = MagicMock()
    collection.find_one = AsyncMock(return_value=existing)
    collection.update_one = AsyncMock()
    db = {"meal_entries": collection}

    with patch("src.services.analytics_service.get_database", return_value=db):
        result = await MealEntryService.update_meal_entry(
            "entry-1",
            MealEntryUpdate(),
            "user-1",
        )

    assert isinstance(result, MealEntry)
    collection.update_one.assert_not_called()


@pytest.mark.asyncio
async def test_meal_entry_service_update_returns_existing_when_refetch_missing():
    existing = _meal_doc(entry_id="entry-1")

    collection = MagicMock()
    collection.find_one = AsyncMock(side_effect=[existing, None])
    collection.update_one = AsyncMock()
    db = {"meal_entries": collection}

    with patch("src.services.analytics_service.get_database", return_value=db), patch(
        "src.services.analytics_service.DailyLogService.recalculate_daily_totals",
        new_callable=AsyncMock,
    ):
        result = await MealEntryService.update_meal_entry(
            "entry-1",
            MealEntryUpdate(note="changed"),
            "user-1",
        )

    assert isinstance(result, MealEntry)


@pytest.mark.asyncio
async def test_meal_entry_service_delete_cases():
    existing = _meal_doc(entry_id="entry-1")

    collection_missing = MagicMock()
    collection_missing.find_one = AsyncMock(return_value=None)
    db_missing = {"meal_entries": collection_missing}

    with patch("src.services.analytics_service.get_database", return_value=db_missing):
        deleted = await MealEntryService.delete_meal_entry("entry-1", "user-1")
    assert deleted is False

    collection_fail = MagicMock()
    collection_fail.find_one = AsyncMock(return_value=existing)
    collection_fail.delete_one = AsyncMock(return_value=SimpleNamespace(deleted_count=0))
    db_fail = {"meal_entries": collection_fail}

    with patch("src.services.analytics_service.get_database", return_value=db_fail):
        deleted = await MealEntryService.delete_meal_entry("entry-1", "user-1")
    assert deleted is False

    collection_ok = MagicMock()
    collection_ok.find_one = AsyncMock(return_value=existing)
    collection_ok.delete_one = AsyncMock(return_value=SimpleNamespace(deleted_count=1))
    db_ok = {"meal_entries": collection_ok}

    with patch("src.services.analytics_service.get_database", return_value=db_ok), patch(
        "src.services.analytics_service.DailyLogService.recalculate_daily_totals",
        new_callable=AsyncMock,
    ) as mock_recalc:
        deleted = await MealEntryService.delete_meal_entry("entry-1", "user-1")

    assert deleted is True
    mock_recalc.assert_awaited_once_with("user-1", existing["date"])
