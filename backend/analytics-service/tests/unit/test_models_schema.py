from pydantic import ValidationError

from src.models.daily_log import DailyLog
from src.models.meal_entry import MacroNutrients, MealEntry, MealIngredient, MealType


def test_daily_log_model_uses_mongo_aliases_and_macro_defaults():
    log = DailyLog(user_id="user-1", date="2026-03-20")

    payload = log.model_dump(by_alias=True)

    assert "_id" in payload
    assert "_created_at" in payload
    assert "_updated_at" in payload
    assert payload["total_macros"] == {
        "calories": 0.0,
        "proteins": 0.0,
        "carbs": 0.0,
        "fats": 0.0,
    }


def test_meal_entry_model_persists_denormalized_ingredient_snapshot():
    entry = MealEntry(
        user_id="user-1",
        daily_log_id="log-1",
        date="2026-03-20",
        meal_type=MealType.DINNER,
        ingredients=[
            MealIngredient(
                ingredient_id="ingredient-1",
                name="Rice",
                quantity=120.0,
                macros=MacroNutrients(calories=156.0, proteins=3.0, carbs=35.0, fats=0.3),
            )
        ],
        total_macros=MacroNutrients(calories=156.0, proteins=3.0, carbs=35.0, fats=0.3),
        recipe_id="recipe-1",
        recipe_name="Rice Bowl",
    )

    payload = entry.model_dump(by_alias=True)

    assert payload["_id"]
    assert payload["ingredients"][0]["ingredient_id"] == "ingredient-1"
    assert payload["ingredients"][0]["name"] == "Rice"
    assert payload["total_macros"]["calories"] == 156.0


def test_daily_log_model_rejects_negative_goal_values():
    try:
        DailyLog(user_id="user-1", date="2026-03-20", calorie_goal=-10.0)
    except ValidationError as exc:
        assert "calorie_goal" in str(exc)
    else:
        raise AssertionError("Expected validation error for negative calorie_goal")
