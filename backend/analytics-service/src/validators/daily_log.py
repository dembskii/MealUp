from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

from src.models.meal_entry import MacroNutrients
from src.validators.meal_entry import MealEntryResponse


class DailyGoalsUpdate(BaseModel):
    """Request schema – updating daily nutrition goals (PATCH)"""
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


class DailyLogResponse(BaseModel):
    """Response schema – serialized daily log returned to the client"""
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
    """Response schema – summary view of a daily log (for weekly/range listings)"""
    date: str
    total_macros: MacroNutrients
    calorie_goal: Optional[float] = None
    meals_count: int = 0
