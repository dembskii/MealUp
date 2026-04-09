from unittest.mock import AsyncMock, patch

from src.models.model import CapacityUnit, Recipe, WeightedIngredient


def _recipe_response_payload(recipe: Recipe) -> dict:
    return recipe.model_dump(by_alias=True, mode="json")


def _sample_recipe(author_id: str = "user-1") -> Recipe:
    return Recipe(
        name="Tomato Pasta",
        author_id=author_id,
        ingredients=[
            WeightedIngredient(
                ingredient_id="ingredient-1",
                capacity=CapacityUnit.GRAM,
                quantity=250.0,
            )
        ],
        prepare_instruction=["Boil water", "Cook pasta", "Add sauce"],
        time_to_prepare=900,
    )


@patch("src.api.routes.RecipeService.get_recipes", new_callable=AsyncMock)
def test_get_recipes_success(mock_get_recipes, client):
    recipe = _sample_recipe()
    mock_get_recipes.return_value = [recipe]

    response = client.get("/recipes/", params={"skip": 2, "limit": 5, "author_id": "user-1"})

    assert response.status_code == 200
    assert response.json() == [_recipe_response_payload(recipe)]
    mock_get_recipes.assert_awaited_once_with(2, 5, "user-1")


@patch("src.api.routes.RecipeService.get_recipes", new_callable=AsyncMock)
def test_get_recipes_returns_500_on_service_error(mock_get_recipes, client):
    mock_get_recipes.side_effect = RuntimeError("query failed")

    response = client.get("/recipes/")

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to get recipes"


@patch("src.api.routes.generate_recipe_image", new_callable=AsyncMock)
@patch("src.api.routes.RecipeService.create_recipe", new_callable=AsyncMock)
def test_create_recipe_success(mock_create_recipe, _mock_generate_image, client):
    recipe = _sample_recipe(author_id="user-abc")
    mock_create_recipe.return_value = recipe

    payload = {
        "name": "Tomato Pasta",
        "ingredients": [
            {
                "ingredient_id": "ingredient-1",
                "capacity": "g",
                "quantity": 250.0,
            }
        ],
        "prepare_instruction": ["Boil water", "Cook pasta", "Add sauce"],
        "time_to_prepare": 900,
    }
    response = client.post(
        "/recipes/",
        json=payload,
        headers={"X-User-Id": "user-abc"},
    )

    assert response.status_code == 201
    assert response.json() == _recipe_response_payload(recipe)
    mock_create_recipe.assert_awaited_once()


def test_create_recipe_requires_x_user_id_header(client):
    payload = {
        "name": "Recipe",
        "ingredients": [{"ingredient_id": "ing-1", "capacity": "g", "quantity": 50}],
        "prepare_instruction": ["Step 1"],
        "time_to_prepare": 120,
    }

    response = client.post("/recipes/", json=payload)

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


@patch("src.api.routes.RecipeService.get_recipe", new_callable=AsyncMock)
def test_get_recipe_success(mock_get_recipe, client):
    recipe = _sample_recipe()
    mock_get_recipe.return_value = recipe

    response = client.get(f"/recipes/{recipe.id}")

    assert response.status_code == 200
    assert response.json() == _recipe_response_payload(recipe)
    mock_get_recipe.assert_awaited_once_with(recipe.id)


@patch("src.api.routes.RecipeService.get_recipe", new_callable=AsyncMock)
def test_get_recipe_not_found(mock_get_recipe, client):
    mock_get_recipe.return_value = None

    response = client.get("/recipes/missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Recipe not found"


@patch("src.api.routes.RecipeService.get_recipe", new_callable=AsyncMock)
def test_get_recipe_internal_requires_token(mock_get_recipe, client):
    response = client.get("/recipes/internal/recipes/recipe-1")

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid internal service token"
    mock_get_recipe.assert_not_awaited()


@patch("src.api.routes.RecipeService.get_recipe", new_callable=AsyncMock)
def test_get_recipe_internal_success(mock_get_recipe, client):
    recipe = _sample_recipe()
    mock_get_recipe.return_value = recipe

    response = client.get(
        f"/recipes/internal/recipes/{recipe.id}",
        headers={"X-Internal-Token": "mealup-internal-dev-token"},
    )

    assert response.status_code == 200
    assert response.json() == _recipe_response_payload(recipe)


@patch("src.api.routes.RecipeService.update_recipe", new_callable=AsyncMock)
def test_update_recipe_success(mock_update_recipe, client):
    recipe = _sample_recipe(author_id="author-1")
    mock_update_recipe.return_value = recipe

    response = client.put(
        f"/recipes/{recipe.id}",
        json={"time_to_prepare": 1000},
        headers={"X-User-Id": "author-1"},
    )

    assert response.status_code == 200
    assert response.json() == _recipe_response_payload(recipe)
    mock_update_recipe.assert_awaited_once()


@patch("src.api.routes.RecipeService.update_recipe", new_callable=AsyncMock)
def test_update_recipe_not_found_or_forbidden(mock_update_recipe, client):
    mock_update_recipe.return_value = None

    response = client.put(
        "/recipes/recipe-1",
        json={"time_to_prepare": 1000},
        headers={"X-User-Id": "different-author"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Recipe not found or you don't have permission to update it"


def test_update_recipe_requires_x_user_id_header(client):
    response = client.put("/recipes/recipe-1", json={"time_to_prepare": 1000})

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


@patch("src.api.routes.RecipeService.delete_recipe", new_callable=AsyncMock)
def test_delete_recipe_success(mock_delete_recipe, client):
    mock_delete_recipe.return_value = True

    response = client.delete("/recipes/recipe-1", headers={"X-User-Id": "author-1"})

    assert response.status_code == 204
    assert response.content == b""
    mock_delete_recipe.assert_awaited_once_with("recipe-1", "author-1")


@patch("src.api.routes.RecipeService.delete_recipe", new_callable=AsyncMock)
def test_delete_recipe_not_found_or_forbidden(mock_delete_recipe, client):
    mock_delete_recipe.return_value = False

    response = client.delete("/recipes/recipe-1", headers={"X-User-Id": "other"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Recipe not found or you don't have permission to delete it"


@patch("src.api.routes.RecipeService.like_recipe", new_callable=AsyncMock)
def test_like_recipe_success(mock_like_recipe, client):
    recipe = _sample_recipe()
    mock_like_recipe.return_value = recipe

    response = client.post("/recipes/recipe-1/like")

    assert response.status_code == 200
    assert response.json() == _recipe_response_payload(recipe)
    mock_like_recipe.assert_awaited_once_with("recipe-1")


@patch("src.api.routes.RecipeService.like_recipe", new_callable=AsyncMock)
def test_like_recipe_not_found(mock_like_recipe, client):
    mock_like_recipe.return_value = None

    response = client.post("/recipes/missing/like")

    assert response.status_code == 404
    assert response.json()["detail"] == "Recipe not found"


@patch("src.api.routes.RecipeService.unlike_recipe", new_callable=AsyncMock)
def test_unlike_recipe_success(mock_unlike_recipe, client):
    recipe = _sample_recipe()
    mock_unlike_recipe.return_value = recipe

    response = client.post("/recipes/recipe-1/unlike")

    assert response.status_code == 200
    assert response.json() == _recipe_response_payload(recipe)
    mock_unlike_recipe.assert_awaited_once_with("recipe-1")


@patch("src.api.routes.RecipeService.unlike_recipe", new_callable=AsyncMock)
def test_unlike_recipe_not_found(mock_unlike_recipe, client):
    mock_unlike_recipe.return_value = None

    response = client.post("/recipes/missing/unlike")

    assert response.status_code == 404
    assert response.json()["detail"] == "Recipe not found"


@patch("src.api.routes.RecipeService.search_recipes", new_callable=AsyncMock)
def test_search_recipes_success(mock_search_recipes, client):
    recipe = _sample_recipe(author_id="author-x")
    mock_search_recipes.return_value = [recipe]

    response = client.get(
        "/recipes/search",
        params={"q": "pasta", "author_id": "author-x", "skip": 0, "limit": 10},
    )

    assert response.status_code == 200
    assert response.json() == [_recipe_response_payload(recipe)]
    mock_search_recipes.assert_awaited_once_with(
        query="pasta",
        tags=None,
        author_id="author-x",
        skip=0,
        limit=10,
    )


@patch("src.api.routes.RecipeService.search_recipes", new_callable=AsyncMock)
def test_search_recipes_returns_500_on_service_error(mock_search_recipes, client):
    mock_search_recipes.side_effect = RuntimeError("search failure")

    response = client.get("/recipes/search", params={"q": "pasta"})

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to search recipes"
