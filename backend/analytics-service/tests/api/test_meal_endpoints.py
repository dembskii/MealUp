from unittest.mock import AsyncMock, patch

from src.models.meal_entry import MacroNutrients, MealEntry, MealIngredient, MealType


def _sample_meal(*, user_id: str, date: str, daily_log_id: str) -> MealEntry:
    return MealEntry(
        user_id=user_id,
        daily_log_id=daily_log_id,
        date=date,
        meal_type=MealType.BREAKFAST,
        ingredients=[
            MealIngredient(
                ingredient_id="ingredient-1",
                name="Oats",
                quantity=80.0,
                macros=MacroNutrients(calories=310.0, proteins=10.0, carbs=54.0, fats=6.0),
            )
        ],
        recipe_id="recipe-1",
        recipe_name="Protein Oatmeal",
        total_macros=MacroNutrients(calories=310.0, proteins=10.0, carbs=54.0, fats=6.0),
        note="Morning meal",
    )


def _meal_payload(entry: MealEntry) -> dict:
    return entry.model_dump(by_alias=True, mode="json")


@patch("src.api.routes.MealEntryService.create_meal_entry", new_callable=AsyncMock)
def test_create_meal_entry_success(mock_create_meal_entry, client):
    entry = _sample_meal(user_id="gateway-user", date="2026-03-20", daily_log_id="log-1")
    mock_create_meal_entry.return_value = entry

    response = client.post(
        "/analytics/meals",
        json={
            "date": "2026-03-20",
            "meal_type": "breakfast",
            "recipe_id": "recipe-1",
            "note": "Morning meal",
        },
        headers={"X-User-Id": "gateway-user"},
    )

    assert response.status_code == 201
    assert response.json() == _meal_payload(entry)
    mock_create_meal_entry.assert_awaited_once()


@patch("src.api.routes.MealEntryService.create_meal_entry", new_callable=AsyncMock)
def test_create_meal_entry_returns_400_for_invalid_date(mock_create_meal_entry, client):
    response = client.post(
        "/analytics/meals",
        json={
            "date": "20-03-2026",
            "meal_type": "breakfast",
            "recipe_id": "recipe-1",
        },
        headers={"X-User-Id": "gateway-user"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid date format. Expected YYYY-MM-DD"
    mock_create_meal_entry.assert_not_awaited()


@patch("src.api.routes.MealEntryService.create_meal_entry", new_callable=AsyncMock)
def test_create_meal_entry_returns_400_for_domain_error(mock_create_meal_entry, client):
    mock_create_meal_entry.side_effect = ValueError("Recipe recipe-404 not found")

    response = client.post(
        "/analytics/meals",
        json={
            "date": "2026-03-20",
            "meal_type": "breakfast",
            "recipe_id": "recipe-404",
        },
        headers={"X-User-Id": "gateway-user"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Recipe recipe-404 not found"


@patch("src.api.routes.MealEntryService.create_meal_entry", new_callable=AsyncMock)
def test_create_meal_entry_returns_500_for_unexpected_error(mock_create_meal_entry, client):
    mock_create_meal_entry.side_effect = RuntimeError("db timeout")

    response = client.post(
        "/analytics/meals",
        json={
            "date": "2026-03-20",
            "meal_type": "breakfast",
            "recipe_id": "recipe-1",
        },
        headers={"X-User-Id": "gateway-user"},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to create meal entry"


@patch("src.api.routes.MealEntryService.get_meals_for_date", new_callable=AsyncMock)
def test_get_meals_for_date_success(mock_get_meals_for_date, client):
    entry = _sample_meal(user_id="gateway-user", date="2026-03-20", daily_log_id="log-1")
    mock_get_meals_for_date.return_value = [entry]

    response = client.get("/analytics/meals/2026-03-20", headers={"X-User-Id": "gateway-user"})

    assert response.status_code == 200
    assert response.json() == [_meal_payload(entry)]
    mock_get_meals_for_date.assert_awaited_once_with("gateway-user", "2026-03-20")


@patch("src.api.routes.MealEntryService.get_meal_entry", new_callable=AsyncMock)
def test_get_meal_entry_success(mock_get_meal_entry, client):
    entry = _sample_meal(user_id="gateway-user", date="2026-03-20", daily_log_id="log-1")
    mock_get_meal_entry.return_value = entry

    response = client.get("/analytics/meals/entry/entry-1", headers={"X-User-Id": "gateway-user"})

    assert response.status_code == 200
    assert response.json() == _meal_payload(entry)
    mock_get_meal_entry.assert_awaited_once_with("entry-1", "gateway-user")


@patch("src.api.routes.MealEntryService.get_meal_entry", new_callable=AsyncMock)
def test_get_meal_entry_not_found(mock_get_meal_entry, client):
    mock_get_meal_entry.return_value = None

    response = client.get("/analytics/meals/entry/missing", headers={"X-User-Id": "gateway-user"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Meal entry not found"


@patch("src.api.routes.MealEntryService.update_meal_entry", new_callable=AsyncMock)
def test_update_meal_entry_success(mock_update_meal_entry, client):
    updated_entry = _sample_meal(user_id="gateway-user", date="2026-03-20", daily_log_id="log-1")
    updated_entry.note = "Updated note"
    mock_update_meal_entry.return_value = updated_entry

    response = client.put(
        "/analytics/meals/entry/entry-1",
        json={"note": "Updated note"},
        headers={"X-User-Id": "gateway-user"},
    )

    assert response.status_code == 200
    assert response.json() == _meal_payload(updated_entry)
    mock_update_meal_entry.assert_awaited_once()
    update_call = mock_update_meal_entry.await_args.args
    assert update_call[0] == "entry-1"
    assert update_call[2] == "gateway-user"
    assert update_call[1].model_dump(exclude_unset=True) == {"note": "Updated note"}


@patch("src.api.routes.MealEntryService.update_meal_entry", new_callable=AsyncMock)
def test_update_meal_entry_not_found(mock_update_meal_entry, client):
    mock_update_meal_entry.return_value = None

    response = client.put(
        "/analytics/meals/entry/entry-1",
        json={"note": "Updated note"},
        headers={"X-User-Id": "gateway-user"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Meal entry not found or you don't have permission to update it"


@patch("src.api.routes.MealEntryService.delete_meal_entry", new_callable=AsyncMock)
def test_delete_meal_entry_success(mock_delete_meal_entry, client):
    mock_delete_meal_entry.return_value = True

    response = client.delete("/analytics/meals/entry/entry-1", headers={"X-User-Id": "gateway-user"})

    assert response.status_code == 204
    assert response.content == b""
    mock_delete_meal_entry.assert_awaited_once_with("entry-1", "gateway-user")


@patch("src.api.routes.MealEntryService.delete_meal_entry", new_callable=AsyncMock)
def test_delete_meal_entry_not_found(mock_delete_meal_entry, client):
    mock_delete_meal_entry.return_value = False

    response = client.delete("/analytics/meals/entry/entry-1", headers={"X-User-Id": "gateway-user"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Meal entry not found or you don't have permission to delete it"
