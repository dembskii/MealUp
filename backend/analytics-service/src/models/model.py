from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from enum import Enum
from datetime import datetime, date
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
    """A single meal entry (e.g. breakfast, lunch) within a day"""
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


class DailyLog(BaseModel):
    """Daily nutrition log aggregating all meals for a user on a given date"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id", description="Unique log ID")
    user_id: str = Field(..., description="User ID (auth0 sub)")
    date: str = Field(..., description="Date string YYYY-MM-DD")
    total_macros: MacroNutrients = Field(default_factory=MacroNutrients, description="Sum of all meals' macros")
    calorie_goal: Optional[float] = Field(None, ge=0, description="Daily calorie goal (kcal)")
    protein_goal: Optional[float] = Field(None, ge=0, description="Daily protein goal (g)")
    carbs_goal: Optional[float] = Field(None, ge=0, description="Daily carbs goal (g)")
    fats_goal: Optional[float] = Field(None, ge=0, description="Daily fats goal (g)")
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="_created_at")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="_updated_at")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "_id": "d50e8400-e29b-41d4-a716-446655440020",
                "user_id": "google-oauth2|1234567890",
                "date": "2026-02-09",
                "total_macros": {"calories": 1850.0, "proteins": 140.0, "carbs": 200.0, "fats": 55.0},
                "calorie_goal": 2200.0,
                "protein_goal": 150.0,
                "carbs_goal": 250.0,
                "fats_goal": 70.0,
            }
        }
    )


# ============ Request / Response schemas ============

class MealIngredientCreate(BaseModel):
    """Schema for adding an ingredient to a meal"""
    ingredient_id: str = Field(..., description="Ingredient ID from recipe-service")
    name: str = Field(..., min_length=1, max_length=100)
    quantity: float = Field(..., gt=0, description="Quantity in grams")
    macros: MacroNutrients = Field(..., description="Macros for this quantity")


class MealEntryCreate(BaseModel):
    """Schema for creating a new meal entry"""
    date: str = Field(..., description="Date YYYY-MM-DD")
    meal_type: MealType
    ingredients: List[MealIngredientCreate] = Field(default_factory=list)
    recipe_id: Optional[str] = None
    recipe_name: Optional[str] = None
    note: Optional[str] = Field(None, max_length=500)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
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
                "note": "Post-workout meal"
            }
        }
    )


class MealEntryUpdate(BaseModel):
    """Schema for updating a meal entry"""
    meal_type: Optional[MealType] = None
    ingredients: Optional[List[MealIngredientCreate]] = None
    recipe_id: Optional[str] = None
    recipe_name: Optional[str] = None
    note: Optional[str] = Field(None, max_length=500)


class DailyGoalsUpdate(BaseModel):
    """Schema for updating daily nutrition goals"""
    calorie_goal: Optional[float] = Field(None, ge=0)
    protein_goal: Optional[float] = Field(None, ge=0)
    carbs_goal: Optional[float] = Field(None, ge=0)
    fats_goal: Optional[float] = Field(None, ge=0)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "calorie_goal": 2200.0,
                "protein_goal": 150.0,
                "carbs_goal": 250.0,
                "fats_goal": 70.0,
            }
        }
    )


class MealEntryResponse(BaseModel):
    """Response model for a meal entry"""
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


class DailyLogResponse(BaseModel):
    """Response model for a daily log"""
    id: str = Field(..., alias="_id")
    user_id: str
    date: str
    total_macros: MacroNutrients
    calorie_goal: Optional[float] = None
    protein_goal: Optional[float] = None
    carbs_goal: Optional[float] = None
    fats_goal: Optional[float] = None
    meals: List[MealEntryResponse] = Field(default_factory=list, description="Meal entries for the day")
    created_at: datetime = Field(..., alias="_created_at")
    updated_at: datetime = Field(..., alias="_updated_at")

    model_config = ConfigDict(populate_by_name=True)


class DailySummary(BaseModel):
    """Summary view of a daily log (for weekly/range listings)"""
    date: str
    total_macros: MacroNutrients
    calorie_goal: Optional[float] = None
    meals_count: int = 0
