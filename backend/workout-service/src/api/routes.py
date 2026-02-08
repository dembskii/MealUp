import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Header

from src.models.model import (
    # Exercise models
    ExerciseCreate, ExerciseUpdate, ExerciseResponse,
    BodyPart, Advancement, ExerciseCategory,
    # Training models
    TrainingCreate, TrainingUpdate, TrainingResponse, TrainingWithExercises,
    DayOfWeek, TrainingType, StructSet,
    # Workout Plan models
    WorkoutPlanCreate, WorkoutPlanUpdate, WorkoutPlanResponse, WorkoutPlanDetailed
)
from src.services.exercise_service import ExerciseService
from src.services.training_service import TrainingService
from src.services.workout_plan_service import WorkoutPlanService



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


# ============ TRAINING ENDPOINTS ============

@router.get("/trainings", response_model=list[TrainingResponse])
async def get_trainings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    training_type: Optional[TrainingType] = Query(None),
    search: Optional[str] = Query(None)
):
    """Get list of training sessions with optional filters"""
    try:
        trainings = await TrainingService.get_trainings(
            skip=skip,
            limit=limit,
            training_type=training_type,
            search=search
        )
        return trainings
    except Exception as e:
        logger.error(f"Error getting trainings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get trainings")


@router.get("/trainings/{training_id}", response_model=TrainingResponse)
async def get_training(training_id: str):
    """Get a training session by ID"""
    training = await TrainingService.get_training(training_id)
    
    if not training:
        raise HTTPException(status_code=404, detail="Training not found")
    
    return training


@router.get("/trainings/{training_id}/with-exercises", response_model=TrainingWithExercises)
async def get_training_with_exercises(training_id: str):
    """Get a training session with full exercise details"""
    training = await TrainingService.get_training_with_exercises(training_id)
    
    if not training:
        raise HTTPException(status_code=404, detail="Training not found")
    
    return training


@router.post("/trainings", response_model=TrainingResponse, status_code=201)
async def create_training(training_data: TrainingCreate, x_user_id: Optional[str] = Header(None)):
    """Create a new training session"""
    try:
        training = await TrainingService.create_training(training_data, creator_id=x_user_id)
        return training
    except ValueError as e:
        logger.error(f"Validation error creating training: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating training: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create training")


@router.put("/trainings/{training_id}", response_model=TrainingResponse)
async def update_training(
    training_id: str,
    training_update: TrainingUpdate
):
    """Update a training session"""
    try:
        training = await TrainingService.update_training(training_id, training_update)
        
        if not training:
            raise HTTPException(status_code=404, detail="Training not found")
        
        return training
    except ValueError as e:
        logger.error(f"Validation error updating training: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating training: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update training")


@router.delete("/trainings/{training_id}", status_code=204)
async def delete_training(training_id: str):
    """Delete a training session"""
    deleted = await TrainingService.delete_training(training_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Training not found")
    
    return None


# ============ WORKOUT PLAN ENDPOINTS ============

@router.get("/plans", response_model=list[WorkoutPlanResponse])
async def get_workout_plans(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: Optional[str] = Query(None),
    is_public: Optional[bool] = Query(None),
    trainer_id: Optional[str] = Query(None)
):
    """Get list of workout plans with optional filters"""
    try:
        plans = await WorkoutPlanService.get_workout_plans(
            skip=skip,
            limit=limit,
            search=search,
            is_public=is_public,
            trainer_id=trainer_id
        )
        return plans
    except Exception as e:
        logger.error(f"Error getting workout plans: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get workout plans")


@router.get("/plans/my-plans", response_model=list[WorkoutPlanResponse])
async def get_my_workout_plans(
    x_user_id: str = Header(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
):
    """Get all workout plans created by the authenticated user"""
    try:
        plans = await WorkoutPlanService.get_trainer_plans(
            trainer_id=x_user_id,
            skip=skip,
            limit=limit
        )
        return plans
    except Exception as e:
        logger.error(f"Error getting user's workout plans: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get workout plans")


@router.get("/plans/assigned-to-me", response_model=list[WorkoutPlanResponse])
async def get_assigned_workout_plans(
    x_user_id: str = Header(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
):
    """Get all workout plans assigned to the authenticated user"""
    try:
        plans = await WorkoutPlanService.get_client_plans(
            client_id=x_user_id,
            skip=skip,
            limit=limit
        )
        return plans
    except Exception as e:
        logger.error(f"Error getting assigned workout plans: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get workout plans")


@router.get("/plans/{plan_id}", response_model=WorkoutPlanResponse)
async def get_workout_plan(plan_id: str):
    """Get a workout plan by ID"""
    plan = await WorkoutPlanService.get_workout_plan(plan_id)
    
    if not plan:
        raise HTTPException(status_code=404, detail="Workout plan not found")
    
    return plan


@router.get("/plans/{plan_id}/detailed", response_model=WorkoutPlanDetailed)
async def get_workout_plan_detailed(plan_id: str):
    """Get a workout plan with full training and exercise details"""
    plan = await WorkoutPlanService.get_workout_plan_detailed(plan_id)
    
    if not plan:
        raise HTTPException(status_code=404, detail="Workout plan not found")
    
    return plan


@router.post("/plans", response_model=WorkoutPlanResponse, status_code=201)
async def create_workout_plan(
    plan_data: WorkoutPlanCreate,
    x_user_id: str = Header(...)
):
    """Create a new workout plan"""
    try:
        plan = await WorkoutPlanService.create_workout_plan(
            trainer_id=x_user_id,
            plan_data=plan_data
        )
        return plan
    except ValueError as e:
        logger.error(f"Validation error creating workout plan: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating workout plan: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create workout plan")


@router.put("/plans/{plan_id}", response_model=WorkoutPlanResponse)
async def update_workout_plan(
    plan_id: str,
    plan_update: WorkoutPlanUpdate,
    x_user_id: str = Header(...)
):
    """Update a workout plan (only by creator)"""
    try:
        plan = await WorkoutPlanService.update_workout_plan(
            plan_id=plan_id,
            plan_update=plan_update,
            trainer_id=x_user_id
        )
        
        if not plan:
            raise HTTPException(status_code=404, detail="Workout plan not found")
        
        return plan
    except PermissionError as e:
        logger.error(f"Permission denied: {str(e)}")
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        logger.error(f"Validation error updating workout plan: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating workout plan: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update workout plan")


@router.delete("/plans/{plan_id}", status_code=204)
async def delete_workout_plan(
    plan_id: str,
    x_user_id: str = Header(...)
):
    """Delete a workout plan (only by creator)"""
    try:
        deleted = await WorkoutPlanService.delete_workout_plan(
            plan_id=plan_id,
            trainer_id=x_user_id
        )
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Workout plan not found")
        
        return None
    except PermissionError as e:
        logger.error(f"Permission denied: {str(e)}")
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting workout plan: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete workout plan")


@router.post("/plans/{plan_id}/clients/{client_id}", response_model=WorkoutPlanResponse)
async def add_client_to_plan(
    plan_id: str,
    client_id: str,
    x_user_id: str = Header(...)
):
    """Add a client to a workout plan"""
    try:
        plan = await WorkoutPlanService.add_client_to_plan(
            plan_id=plan_id,
            client_id=client_id,
            trainer_id=x_user_id
        )
        
        if not plan:
            raise HTTPException(status_code=404, detail="Workout plan not found")
        
        return plan
    except PermissionError as e:
        logger.error(f"Permission denied: {str(e)}")
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding client to plan: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to add client to plan")


@router.delete("/plans/{plan_id}/clients/{client_id}", response_model=WorkoutPlanResponse)
async def remove_client_from_plan(
    plan_id: str,
    client_id: str,
    x_user_id: str = Header(...)
):
    """Remove a client from a workout plan"""
    try:
        plan = await WorkoutPlanService.remove_client_from_plan(
            plan_id=plan_id,
            client_id=client_id,
            trainer_id=x_user_id
        )
        
        if not plan:
            raise HTTPException(status_code=404, detail="Workout plan not found")
        
        return plan
    except PermissionError as e:
        logger.error(f"Permission denied: {str(e)}")
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error removing client from plan: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to remove client from plan")


@router.post("/plans/{plan_id}/trainings/{training_id}", response_model=WorkoutPlanResponse)
async def add_training_to_plan(
    plan_id: str,
    training_id: str,
    x_user_id: str = Header(...)
):
    """Add a training session to a workout plan"""
    try:
        plan = await WorkoutPlanService.add_training_to_plan(
            plan_id=plan_id,
            training_id=training_id,
            trainer_id=x_user_id
        )
        
        if not plan:
            raise HTTPException(status_code=404, detail="Workout plan not found")
        
        return plan
    except PermissionError as e:
        logger.error(f"Permission denied: {str(e)}")
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding training to plan: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to add training to plan")


@router.delete("/plans/{plan_id}/trainings/{training_id}", response_model=WorkoutPlanResponse)
async def remove_training_from_plan(
    plan_id: str,
    training_id: str,
    x_user_id: str = Header(...)
):
    """Remove a training session from a workout plan"""
    try:
        plan = await WorkoutPlanService.remove_training_from_plan(
            plan_id=plan_id,
            training_id=training_id,
            trainer_id=x_user_id
        )
        
        if not plan:
            raise HTTPException(status_code=404, detail="Workout plan not found")
        
        return plan
    except PermissionError as e:
        logger.error(f"Permission denied: {str(e)}")
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error removing training from plan: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to remove training from plan")


@router.post("/plans/{plan_id}/like", response_model=WorkoutPlanResponse)
async def like_workout_plan(plan_id: str):
    """Like a workout plan"""
    try:
        plan = await WorkoutPlanService.like_workout_plan(plan_id)
        
        if not plan:
            raise HTTPException(status_code=404, detail="Workout plan not found")
        
        return plan
    except Exception as e:
        logger.error(f"Error liking workout plan: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to like workout plan")


@router.post("/plans/{plan_id}/unlike", response_model=WorkoutPlanResponse)
async def unlike_workout_plan(plan_id: str):
    """Unlike a workout plan"""
    try:
        plan = await WorkoutPlanService.unlike_workout_plan(plan_id)
        
        if not plan:
            raise HTTPException(status_code=404, detail="Workout plan not found")
        
        return plan
    except Exception as e:
        logger.error(f"Error unliking workout plan: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to unlike workout plan")
