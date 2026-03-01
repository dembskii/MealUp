import re
from fastapi import HTTPException

from src.validators.meal_entry import (
    MealIngredientCreate,
    MealEntryCreate,
    MealEntryUpdate,
    MealEntryResponse,
)
from src.validators.daily_log import (
    DailyGoalsUpdate,
    DailyLogResponse,
    DailySummary,
)


def validate_date_format(date_str: str) -> str:
    """Validate that the date string is in YYYY-MM-DD format and return it."""
    pattern = r"^\d{4}-\d{2}-\d{2}$"
    if not re.match(pattern, date_str):
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Expected YYYY-MM-DD"
        )
    return date_str


def validate_date_range(date_from: str, date_to: str) -> None:
    """Validate that date_from <= date_to."""
    if date_from > date_to:
        raise HTTPException(
            status_code=400,
            detail="date_from must be earlier than or equal to date_to"
        )
