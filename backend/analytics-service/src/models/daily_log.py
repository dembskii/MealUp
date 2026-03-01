from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
import uuid

from src.models.meal_entry import MacroNutrients


class DailyLog(BaseModel):
    """DB document – daily nutrition log aggregating all meals for a user on a given date.
    Stored in the ``daily_logs`` MongoDB collection.
    """
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
