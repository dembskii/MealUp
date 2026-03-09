from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

from src.models.meal_entry import MealType, MacroNutrients, MealIngredient


class MealIngredientCreate(BaseModel):
    """Request schema – adding a single ingredient to a meal (manual mode).

    Only ingredient_id and quantity are required.
    name and macros are resolved server-side from recipe-service
    but can be supplied as an optional client-side override/cache.
    """
    ingredient_id: str = Field(..., description="Ingredient ID from recipe-service")
    name: Optional[str] = Field(None, max_length=100, description="Ingredient name (auto-resolved if omitted)")
    quantity: float = Field(..., gt=0, description="Quantity in grams")
    macros: Optional[MacroNutrients] = Field(None, description="Pre-computed macros (auto-resolved if omitted)")


class MealEntryCreate(BaseModel):
    """Request schema – creating a new meal entry.

    Two modes of operation:
    1. **By recipe** – provide ``recipe_id``; the server fetches the recipe from
       recipe-service, resolves all ingredients + macros automatically.
       ``ingredients`` can be omitted.
    2. **Manual ingredients** – provide ``ingredients`` list with
       ``ingredient_id`` + ``quantity``; the server fetches macro_per_hundred
       from recipe-service and computes macros for the given quantity.

    At least one of ``recipe_id`` or ``ingredients`` must be provided.
    """
    date: str = Field(..., description="Date YYYY-MM-DD")
    meal_type: MealType
    ingredients: List[MealIngredientCreate] = Field(
        default_factory=list,
        description="Manual ingredient list. Ignored when recipe_id is provided.",
    )
    recipe_id: Optional[str] = Field(
        None,
        description="Recipe ID from recipe-service. When set, ingredients & macros are resolved server-side.",
    )
    recipe_name: Optional[str] = Field(
        None,
        description="Recipe name (auto-resolved from recipe-service if omitted).",
    )
    note: Optional[str] = Field(None, max_length=500)

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "summary": "Add meal by recipe",
                    "value": {
                        "date": "2026-02-09",
                        "meal_type": "lunch",
                        "recipe_id": "650e8400-e29b-41d4-a716-446655440001",
                        "note": "Post-workout meal",
                    },
                },
                {
                    "summary": "Add meal by manual ingredients",
                    "value": {
                        "date": "2026-02-09",
                        "meal_type": "breakfast",
                        "ingredients": [
                            {
                                "ingredient_id": "550e8400-e29b-41d4-a716-446655440000",
                                "quantity": 200.0,
                            }
                        ],
                    },
                },
            ]
        }
    )


class MealEntryUpdate(BaseModel):
    """Request schema – updating a meal entry (PATCH)"""
    meal_type: Optional[MealType] = None
    ingredients: Optional[List[MealIngredientCreate]] = None
    recipe_id: Optional[str] = None
    recipe_name: Optional[str] = None
    note: Optional[str] = Field(None, max_length=500)


class MealEntryResponse(BaseModel):
    """Response schema – serialized meal entry returned to the client"""
    id: str = Field(..., alias="_id")
    user_id: str
    daily_log_id: str
    date: str
    meal_type: MealType
    ingredients: List[MealIngredient]
    recipe_id: Optional[str] = None
    recipe_name: Optional[str] = None
    total_macros: MacroNutrients
    note: Optional[str] = None
    created_at: datetime = Field(..., alias="_created_at")
    updated_at: datetime = Field(..., alias="_updated_at")

    model_config = ConfigDict(populate_by_name=True)
