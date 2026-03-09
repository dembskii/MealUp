from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from enum import Enum
from datetime import datetime
import uuid


class MealType(str, Enum):
    """Enum for meal types"""
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class MacroNutrients(BaseModel):
    """Macronutrient breakdown"""
    calories: float = Field(0.0, ge=0, description="Total calories (kcal)")
    proteins: float = Field(0.0, ge=0, description="Proteins in grams")
    carbs: float = Field(0.0, ge=0, description="Carbohydrates in grams")
    fats: float = Field(0.0, ge=0, description="Fats in grams")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "calories": 450.0,
                "proteins": 30.0,
                "carbs": 50.0,
                "fats": 12.0,
            }
        }
    )


class MealIngredient(BaseModel):
    """An ingredient consumed within a meal entry, with quantity and computed macros"""
    ingredient_id: str = Field(..., description="ID reference to the ingredient from recipe-service")
    name: str = Field(..., min_length=1, max_length=100, description="Ingredient name (denormalized)")
    quantity: float = Field(..., gt=0, description="Amount consumed in grams")
    macros: MacroNutrients = Field(..., description="Computed macros for this quantity")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ingredient_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Chicken Breast",
                "quantity": 200.0,
                "macros": {
                    "calories": 330.0,
                    "proteins": 62.0,
                    "carbs": 0.0,
                    "fats": 7.2,
                }
            }
        }
    )


class MealEntry(BaseModel):
    """DB document – single meal entry (e.g. breakfast, lunch) within a day.
    Stored in the ``meal_entries`` MongoDB collection.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id", description="Unique entry ID")
    user_id: str = Field(..., description="User ID (auth0 sub)")
    daily_log_id: str = Field(..., description="Reference to the parent daily log")
    date: str = Field(..., description="Date string YYYY-MM-DD")
    meal_type: MealType = Field(..., description="Type of meal")
    ingredients: List[MealIngredient] = Field(default_factory=list, description="Ingredients consumed")
    recipe_id: Optional[str] = Field(None, description="Optional reference to a recipe from recipe-service")
    recipe_name: Optional[str] = Field(None, description="Optional recipe name (denormalized)")
    total_macros: MacroNutrients = Field(default_factory=MacroNutrients, description="Aggregated macros for this meal")
    note: Optional[str] = Field(None, max_length=500, description="Optional note")
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="_created_at")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="_updated_at")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "_id": "a50e8400-e29b-41d4-a716-446655440010",
                "user_id": "google-oauth2|1234567890",
                "daily_log_id": "d50e8400-e29b-41d4-a716-446655440020",
                "date": "2026-02-09",
                "meal_type": "lunch",
                "ingredients": [
                    {
                        "ingredient_id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "Chicken Breast",
                        "quantity": 200.0,
                        "macros": {"calories": 330.0, "proteins": 62.0, "carbs": 0.0, "fats": 7.2}
                    }
                ],
                "recipe_id": None,
                "recipe_name": None,
                "total_macros": {"calories": 330.0, "proteins": 62.0, "carbs": 0.0, "fats": 7.2},
                "note": "Post-workout meal",
            }
        }
    )
