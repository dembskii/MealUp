from unittest.mock import AsyncMock, patch

from src.models.daily_log import DailyLog
from src.models.meal_entry import MacroNutrients, MealEntry, MealIngredient, MealType


def _sample_meal(
    *,
    user_id: str,
    date: str,
    daily_log_id: str,
    ingredient_id: str = "ingredient-1",
) -> MealEntry:
    return MealEntry(
        user_id=user_id,
        daily_log_id=daily_log_id,
        date=date,
        meal_type=MealType.LUNCH,
        ingredients=[
            MealIngredient(
                ingredient_id=ingredient_id,
                name="Chicken Breast",
                quantity=150.0,
                macros=MacroNutrients(calories=220.0, proteins=32.0, carbs=0.0, fats=5.0),
            )
        ],
        total_macros=MacroNutrients(calories=220.0, proteins=32.0, carbs=0.0, fats=5.0),
        note="Lunch entry",
    )


def _sample_daily_log(*, user_id: str, date: str) -> DailyLog:
    return DailyLog(
        user_id=user_id,
        date=date,
        total_macros=MacroNutrients(calories=220.0, proteins=32.0, carbs=0.0, fats=5.0),
        calorie_goal=2200.0,
        protein_goal=150.0,
    )


def _daily_log_response_payload(log: DailyLog, meals: list[MealEntry]) -> dict:
    payload = log.model_dump(by_alias=True, mode="json")
    payload["meals"] = [meal.model_dump(by_alias=True, mode="json") for meal in meals]
    return payload


@patch("src.api.routes.MealEntryService.get_meals_for_date", new_callable=AsyncMock)
@patch("src.api.routes.DailyLogService.get_or_create_daily_log", new_callable=AsyncMock)
def test_get_daily_log_success(mock_get_log, mock_get_meals, client):
    log = _sample_daily_log(user_id="gateway-user", date="2026-03-20")
    meal = _sample_meal(user_id="gateway-user", date="2026-03-20", daily_log_id=log.id)

    mock_get_log.return_value = log
    mock_get_meals.return_value = [meal]

    response = client.get("/analytics/daily/2026-03-20", headers={"X-User-Id": "gateway-user"})

    assert response.status_code == 200
    assert response.json() == _daily_log_response_payload(log, [meal])
    mock_get_log.assert_awaited_once_with("gateway-user", "2026-03-20")
    mock_get_meals.assert_awaited_once_with("gateway-user", "2026-03-20")


@patch("src.api.routes.MealEntryService.get_meals_for_date", new_callable=AsyncMock)
@patch("src.api.routes.DailyLogService.get_or_create_daily_log", new_callable=AsyncMock)
def test_get_daily_log_uses_jwt_sub_when_header_missing(mock_get_log, mock_get_meals, client):
    log = _sample_daily_log(user_id="test-user-sub", date="2026-03-20")
    mock_get_log.return_value = log
    mock_get_meals.return_value = []

    response = client.get("/analytics/daily/2026-03-20")

    assert response.status_code == 200
    assert response.json() == _daily_log_response_payload(log, [])
    mock_get_log.assert_awaited_once_with("test-user-sub", "2026-03-20")


@patch("src.api.routes.DailyLogService.get_or_create_daily_log", new_callable=AsyncMock)
def test_get_daily_log_returns_400_for_invalid_date(mock_get_log, client):
    response = client.get("/analytics/daily/20-03-2026", headers={"X-User-Id": "gateway-user"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid date format. Expected YYYY-MM-DD"
    mock_get_log.assert_not_awaited()


@patch("src.api.routes.MealEntryService.get_meals_for_date", new_callable=AsyncMock)
@patch("src.api.routes.DailyLogService.get_daily_logs_range", new_callable=AsyncMock)
def test_get_daily_logs_range_success(mock_get_logs_range, mock_get_meals, client):
    first_log = _sample_daily_log(user_id="gateway-user", date="2026-03-19")
    second_log = _sample_daily_log(user_id="gateway-user", date="2026-03-20")

    first_meal = _sample_meal(user_id="gateway-user", date="2026-03-19", daily_log_id=first_log.id)

    mock_get_logs_range.return_value = [first_log, second_log]
    mock_get_meals.side_effect = [[first_meal], []]

    response = client.get(
        "/analytics/daily",
        params={"date_from": "2026-03-19", "date_to": "2026-03-20"},
        headers={"X-User-Id": "gateway-user"},
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "date": "2026-03-19",
            "total_macros": first_log.total_macros.model_dump(mode="json"),
            "calorie_goal": 2200.0,
            "meals_count": 1,
        },
        {
            "date": "2026-03-20",
            "total_macros": second_log.total_macros.model_dump(mode="json"),
            "calorie_goal": 2200.0,
            "meals_count": 0,
        },
    ]
    mock_get_logs_range.assert_awaited_once_with("gateway-user", "2026-03-19", "2026-03-20")


@patch("src.api.routes.DailyLogService.get_daily_logs_range", new_callable=AsyncMock)
def test_get_daily_logs_range_returns_400_for_invalid_order(mock_get_logs_range, client):
    response = client.get(
        "/analytics/daily",
        params={"date_from": "2026-03-21", "date_to": "2026-03-20"},
        headers={"X-User-Id": "gateway-user"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "date_from must be earlier than or equal to date_to"
    mock_get_logs_range.assert_not_awaited()


@patch("src.api.routes.MealEntryService.get_meals_for_date", new_callable=AsyncMock)
@patch("src.api.routes.DailyLogService.update_goals", new_callable=AsyncMock)
def test_update_daily_goals_success(mock_update_goals, mock_get_meals, client):
    updated_log = _sample_daily_log(user_id="gateway-user", date="2026-03-20")
    meal = _sample_meal(user_id="gateway-user", date="2026-03-20", daily_log_id=updated_log.id)

    mock_update_goals.return_value = updated_log
    mock_get_meals.return_value = [meal]

    payload = {"calorie_goal": 2300.0, "protein_goal": 165.0}
    response = client.put(
        "/analytics/daily/2026-03-20/goals",
        json=payload,
        headers={"X-User-Id": "gateway-user"},
    )

    assert response.status_code == 200
    assert response.json() == _daily_log_response_payload(updated_log, [meal])
    mock_update_goals.assert_awaited_once()
    update_call = mock_update_goals.await_args.args
    assert update_call[0] == "gateway-user"
    assert update_call[1] == "2026-03-20"


@patch("src.api.routes.DailyLogService.update_goals", new_callable=AsyncMock)
def test_update_daily_goals_returns_500_when_service_fails(mock_update_goals, client):
    mock_update_goals.return_value = None

    response = client.put(
        "/analytics/daily/2026-03-20/goals",
        json={"calorie_goal": 2200.0},
        headers={"X-User-Id": "gateway-user"},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to update goals"
