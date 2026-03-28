import pytest
from pydantic import ValidationError

from src.models.model import CapacityUnit, Ingredient, Recipe, RecipeCreate, WeightedIngredient


def test_ingredient_model_uses_db_aliases_and_defaults():
    ingredient = Ingredient(name="Tomato", units="g")

    dumped = ingredient.model_dump(by_alias=True)

    assert "_id" in dumped
    assert dumped["name"] == "Tomato"
    assert dumped["units"] == "g"
    assert "_created_at" in dumped
    assert "_updated_at" in dumped


def test_recipe_model_schema_for_db_document():
    recipe = Recipe(
        name="Quick Salad",
        author_id="user-1",
        ingredients=[
            WeightedIngredient(
                ingredient_id="ingredient-1",
                capacity=CapacityUnit.GRAM,
                quantity=120.5,
            )
        ],
        prepare_instruction=["Wash vegetables", "Mix everything"],
        time_to_prepare=300,
    )

    dumped = recipe.model_dump(by_alias=True)

    assert dumped["_id"]
    assert dumped["author_id"] == "user-1"
    assert dumped["total_likes"] == 0
    assert dumped["ingredients"][0]["capacity"] == "g"


def test_recipe_create_rejects_non_positive_time_to_prepare():
    with pytest.raises(ValidationError):
        RecipeCreate(
            name="Invalid Recipe",
            ingredients=[
                {
                    "ingredient_id": "ingredient-1",
                    "capacity": "g",
                    "quantity": 20,
                }
            ],
            prepare_instruction=["Do something"],
            time_to_prepare=0,
        )


def test_weighted_ingredient_rejects_invalid_quantity():
    with pytest.raises(ValidationError):
        WeightedIngredient(
            ingredient_id="ingredient-1",
            capacity="g",
            quantity=0,
        )


def test_weighted_ingredient_rejects_invalid_capacity_unit():
    with pytest.raises(ValidationError):
        WeightedIngredient(
            ingredient_id="ingredient-1",
            capacity="invalid-unit",
            quantity=50,
        )
