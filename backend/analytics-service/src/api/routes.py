import logging
from typing import Optional, Dict
from fastapi import APIRouter, HTTPException, Query, Header, Depends

from src.validators.meal_entry import MealEntryCreate, MealEntryUpdate, MealEntryResponse
from src.validators.daily_log import DailyLogResponse, DailyGoalsUpdate, DailySummary
from src.services.analytics_service import DailyLogService, MealEntryService
from src.validators import validate_date_format, validate_date_range

from common.auth_guard import require_auth

logger = logging.getLogger(__name__)
router = APIRouter()


def get_user_id_from_header(x_user_id: Optional[str] = Header(None)) -> str:
    """Extract user ID from header (set by gateway after auth)"""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    return x_user_id


# ============ DAILY LOG ENDPOINTS ============

@router.get("/daily/{date}", response_model=DailyLogResponse)
async def get_daily_log(
    date: str,
    x_user_id: str = Header(None, alias="X-User-Id"),
    token_payload: Dict = Depends(require_auth),
):
    """Get the daily nutrition log for a specific date, including all meals."""
    user_id = get_user_id_from_header(x_user_id)
    validate_date_format(date)

    daily_log = await DailyLogService.get_or_create_daily_log(user_id, date)
    meals = await MealEntryService.get_meals_for_date(user_id, date)

    log_dict = daily_log.model_dump(by_alias=True)
    log_dict["meals"] = [m.model_dump(by_alias=True) for m in meals]
    return log_dict



@router.get("/daily", response_model=list[DailySummary])
async def get_daily_logs_range(
    date_from: str = Query(..., description="Start date YYYY-MM-DD"),
    date_to: str = Query(..., description="End date YYYY-MM-DD"),
    x_user_id: str = Header(None, alias="X-User-Id"),
    token_payload: Dict = Depends(require_auth),
):
    """Get daily summaries for a date range."""
    user_id = get_user_id_from_header(x_user_id)
    validate_date_format(date_from)
    validate_date_format(date_to)
    validate_date_range(date_from, date_to)

    logs = await DailyLogService.get_daily_logs_range(user_id, date_from, date_to)

    summaries = []
    for log in logs:
        meals = await MealEntryService.get_meals_for_date(user_id, log.date)
        summaries.append(DailySummary(
            date=log.date,
            total_macros=log.total_macros,
            calorie_goal=log.calorie_goal,
            meals_count=len(meals),
        ))
    return summaries



@router.put("/daily/{date}/goals", response_model=DailyLogResponse)
async def update_daily_goals(
    date: str,
    goals: DailyGoalsUpdate,
    x_user_id: str = Header(None, alias="X-User-Id"),
    token_payload: Dict = Depends(require_auth),
):
    """Set or update daily calorie/macro goals."""
    user_id = get_user_id_from_header(x_user_id)
    validate_date_format(date)

    updated_log = await DailyLogService.update_goals(user_id, date, goals)
    if not updated_log:
        raise HTTPException(status_code=500, detail="Failed to update goals")

    meals = await MealEntryService.get_meals_for_date(user_id, date)
    log_dict = updated_log.model_dump(by_alias=True)
    log_dict["meals"] = [m.model_dump(by_alias=True) for m in meals]
    return log_dict


# ============ MEAL ENTRY ENDPOINTS ============

@router.post("/meals", response_model=MealEntryResponse, status_code=201)
async def create_meal_entry(
    meal_data: MealEntryCreate,
    x_user_id: str = Header(None, alias="X-User-Id"),
    token_payload: Dict = Depends(require_auth),
):
    """Register a new meal entry (breakfast, lunch, dinner, snack)."""
    user_id = get_user_id_from_header(x_user_id)
    validate_date_format(meal_data.date)

    try:
        entry = await MealEntryService.create_meal_entry(meal_data, user_id)
        return entry.model_dump(by_alias=True)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating meal entry: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create meal entry")


@router.get("/meals/{date}", response_model=list[MealEntryResponse])
async def get_meals_for_date(
    date: str,
    x_user_id: str = Header(None, alias="X-User-Id"),
    token_payload: Dict = Depends(require_auth),
):
    """Get all meal entries for a specific date."""
    user_id = get_user_id_from_header(x_user_id)
    validate_date_format(date)

    meals = await MealEntryService.get_meals_for_date(user_id, date)
    return [m.model_dump(by_alias=True) for m in meals]


@router.get("/meals/entry/{entry_id}", response_model=MealEntryResponse)
async def get_meal_entry(
    entry_id: str,
    x_user_id: str = Header(None, alias="X-User-Id"),
    token_payload: Dict = Depends(require_auth),
):
    """Get a specific meal entry by ID."""
    user_id = get_user_id_from_header(x_user_id)

    entry = await MealEntryService.get_meal_entry(entry_id, user_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Meal entry not found")
    return entry.model_dump(by_alias=True)


@router.put("/meals/entry/{entry_id}", response_model=MealEntryResponse)
async def update_meal_entry(
    entry_id: str,
    update_data: MealEntryUpdate,
    x_user_id: str = Header(None, alias="X-User-Id"),
    token_payload: Dict = Depends(require_auth),
):
    """Update a meal entry."""
    user_id = get_user_id_from_header(x_user_id)

    entry = await MealEntryService.update_meal_entry(entry_id, update_data, user_id)
    if not entry:
        raise HTTPException(
            status_code=404,
            detail="Meal entry not found or you don't have permission to update it"
        )
    return entry.model_dump(by_alias=True)


@router.delete("/meals/entry/{entry_id}", status_code=204)
async def delete_meal_entry(
    entry_id: str,
    x_user_id: str = Header(None, alias="X-User-Id"),
    token_payload: Dict = Depends(require_auth),
):
    """Delete a meal entry."""
    user_id = get_user_id_from_header(x_user_id)

    deleted = await MealEntryService.delete_meal_entry(entry_id, user_id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Meal entry not found or you don't have permission to delete it"
        )
    return None
