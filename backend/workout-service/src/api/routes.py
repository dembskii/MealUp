import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Header

from src.models.model import (
    # Exercise models
    ExerciseCreate, ExerciseUpdate, ExerciseResponse,
    BodyPart, Advancement, ExerciseCategory,
    # Training models
    TrainingCreate, TrainingUpdate, TrainingResponse,
    DayOfWeek, TrainingType, StructSet,
    # Workout Plan models
    WorkoutPlanCreate, WorkoutPlanUpdate, WorkoutPlanResponse
)
from src.services.exercise_service import ExerciseService



logger = logging.getLogger(__name__)
router = APIRouter()


def get_user_id_from_header(x_user_id: Optional[str] = Header(None)) -> str:
    """Extract user ID from header (set by gateway after auth)"""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    return x_user_id


# ============ EXERCISE ENDPOINTS ============

@router.get("/exercises", response_model=list[ExerciseResponse])
async def get_exercises(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: Optional[str] = Query(None),
    body_part: Optional[BodyPart] = Query(None),
    advancement: Optional[Advancement] = Query(None),
    category: Optional[ExerciseCategory] = Query(None)
):
    """Get list of exercises with optional filters"""
    try:
        exercises = await ExerciseService.get_exercises(
            skip=skip,
            limit=limit,
            search=search,
            body_part=body_part,
            advancement=advancement,
            category=category
        )
        return exercises
    except Exception as e:
        logger.error(f"Error getting exercises: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get exercises")


@router.get("/exercises/{exercise_id}", response_model=ExerciseResponse)
async def get_exercise(exercise_id: str):
    """Get an exercise by ID"""
    exercise = await ExerciseService.get_exercise(exercise_id)
    
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    
    return exercise


@router.post("/exercises", response_model=ExerciseResponse, status_code=201)
async def create_exercise(exercise_data: ExerciseCreate):
    """Create a new exercise"""
    try:
        exercise = await ExerciseService.create_exercise(exercise_data)
        return exercise
    except Exception as e:
        logger.error(f"Error creating exercise: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create exercise")


@router.put("/exercises/{exercise_id}", response_model=ExerciseResponse)
async def update_exercise(
    exercise_id: str,
    exercise_update: ExerciseUpdate
):
    """Update an exercise"""
    exercise = await ExerciseService.update_exercise(exercise_id, exercise_update)
    
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    
    return exercise


@router.delete("/exercises/{exercise_id}", status_code=204)
async def delete_exercise(exercise_id: str):
    """Delete an exercise"""
    deleted = await ExerciseService.delete_exercise(exercise_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Exercise not found")
    
    return None


@router.get("/exercises/search", response_model=list[ExerciseResponse])
async def search_exercises(
    q: str = Query(..., min_length=1, max_length=200, description="Search query"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    body_part: Optional[BodyPart] = Query(None),
    advancement: Optional[Advancement] = Query(None),
    category: Optional[ExerciseCategory] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """Search exercises by name, description, or filters"""
    try:
        exercises = await ExerciseService.search_exercises(
            query=q,
            tags=tags,
            body_part=body_part,
            advancement=advancement,
            category=category,
            skip=skip,
            limit=limit
        )
        return exercises
    except Exception as e:
        logger.error(f"Error searching exercises: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search exercises")













# ============ ENUM ENDPOINTS (for frontend dropdown values) ============

@router.get("/enums/body-parts")
async def get_body_parts():
    """Get all available body parts"""
    return [{"value": bp.value, "name": bp.name} for bp in BodyPart]


@router.get("/enums/advancements")
async def get_advancements():
    """Get all advancement levels"""
    return [{"value": adv.value, "name": adv.name} for adv in Advancement]


@router.get("/enums/categories")
async def get_categories():
    """Get all exercise categories"""
    return [{"value": cat.value, "name": cat.name} for cat in ExerciseCategory]


@router.get("/enums/training-types")
async def get_training_types():
    """Get all training types"""
    return [{"value": tt.value, "name": tt.name} for tt in TrainingType]


@router.get("/enums/days")
async def get_days_of_week():
    """Get all days of the week"""
    return [{"value": day.value, "name": day.name} for day in DayOfWeek]
