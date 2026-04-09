from unittest.mock import AsyncMock, patch

from src.models.model import Ingredient


def _ingredient_response_payload(ingredient: Ingredient) -> dict:
    return ingredient.model_dump(by_alias=True, mode="json")


@patch("src.api.routes.IngredientService.get_ingredients", new_callable=AsyncMock)
def test_get_ingredients_success(mock_get_ingredients, client):
    ingredient = Ingredient(name="Tomato", units="g")
    mock_get_ingredients.return_value = [ingredient]

    response = client.get("/recipes/ingredients", params={"skip": 1, "limit": 20, "search": "tom"})

    assert response.status_code == 200
    assert response.json() == [_ingredient_response_payload(ingredient)]
    mock_get_ingredients.assert_awaited_once_with(1, 20, "tom")


@patch("src.api.routes.IngredientService.get_ingredients", new_callable=AsyncMock)
def test_get_ingredients_returns_500_on_service_error(mock_get_ingredients, client):
    mock_get_ingredients.side_effect = RuntimeError("db down")

    response = client.get("/recipes/ingredients")

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to get ingredients"


@patch("src.api.routes.IngredientService.get_ingredient", new_callable=AsyncMock)
def test_get_ingredient_success(mock_get_ingredient, client):
    ingredient = Ingredient(name="Salt", units="g")
    mock_get_ingredient.return_value = ingredient

    response = client.get(f"/recipes/ingredients/{ingredient.id}")

    assert response.status_code == 200
    assert response.json() == _ingredient_response_payload(ingredient)
    mock_get_ingredient.assert_awaited_once_with(ingredient.id)


@patch("src.api.routes.IngredientService.get_ingredient", new_callable=AsyncMock)
def test_get_ingredient_not_found(mock_get_ingredient, client):
    mock_get_ingredient.return_value = None

    response = client.get("/recipes/ingredients/missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Ingredient not found"


@patch("src.api.routes.IngredientService.get_ingredient", new_callable=AsyncMock)
def test_get_ingredient_internal_requires_token(mock_get_ingredient, client):
    response = client.get("/recipes/internal/ingredients/ing-1")

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid internal service token"
    mock_get_ingredient.assert_not_awaited()


@patch("src.api.routes.IngredientService.get_ingredient", new_callable=AsyncMock)
def test_get_ingredient_internal_success(mock_get_ingredient, client):
    ingredient = Ingredient(name="Olive Oil", units="ml")
    mock_get_ingredient.return_value = ingredient

    response = client.get(
        f"/recipes/internal/ingredients/{ingredient.id}",
        headers={"X-Internal-Token": "mealup-internal-dev-token"},
    )

    assert response.status_code == 200
    assert response.json() == _ingredient_response_payload(ingredient)


@patch("src.api.routes.IngredientService.create_ingredient", new_callable=AsyncMock)
def test_create_ingredient_success(mock_create_ingredient, client):
    ingredient = Ingredient(name="Flour", units="g")
    mock_create_ingredient.return_value = ingredient

    payload = {
        "name": "Flour",
        "units": "g",
        "macro_per_hundred": {
            "calories": 364,
            "carbs": 76.3,
            "proteins": 10.3,
            "fats": 1.0,
        },
    }
    response = client.post("/recipes/ingredients", json=payload)

    assert response.status_code == 201
    assert response.json() == _ingredient_response_payload(ingredient)


@patch("src.api.routes.IngredientService.create_ingredient", new_callable=AsyncMock)
def test_create_ingredient_returns_500_on_service_error(mock_create_ingredient, client):
    mock_create_ingredient.side_effect = RuntimeError("insert failed")

    response = client.post("/recipes/ingredients", json={"name": "Pepper", "units": "g"})

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to create ingredient"


@patch("src.api.routes.IngredientService.update_ingredient", new_callable=AsyncMock)
def test_update_ingredient_success(mock_update_ingredient, client):
    ingredient = Ingredient(name="Sugar", units="g")
    updated = Ingredient(_id=ingredient.id, name="Brown Sugar", units="g")
    mock_update_ingredient.return_value = updated

    response = client.put(
        f"/recipes/ingredients/{ingredient.id}",
        json={"name": "Brown Sugar"},
    )

    assert response.status_code == 200
    assert response.json() == _ingredient_response_payload(updated)
    mock_update_ingredient.assert_awaited_once()


@patch("src.api.routes.IngredientService.update_ingredient", new_callable=AsyncMock)
def test_update_ingredient_not_found(mock_update_ingredient, client):
    mock_update_ingredient.return_value = None

    response = client.put("/recipes/ingredients/missing", json={"name": "Updated"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Ingredient not found"


@patch("src.api.routes.IngredientService.delete_ingredient", new_callable=AsyncMock)
def test_delete_ingredient_success(mock_delete_ingredient, client):
    mock_delete_ingredient.return_value = True

    response = client.delete("/recipes/ingredients/ing-1")

    assert response.status_code == 204
    assert response.content == b""
    mock_delete_ingredient.assert_awaited_once_with("ing-1")


@patch("src.api.routes.IngredientService.delete_ingredient", new_callable=AsyncMock)
def test_delete_ingredient_not_found(mock_delete_ingredient, client):
    mock_delete_ingredient.return_value = False

    response = client.delete("/recipes/ingredients/missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Ingredient not found"
