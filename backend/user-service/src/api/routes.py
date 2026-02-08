from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.main import get_session
from src.models.model import User
from src.services.user_service import UserService
from src.validators.schema import (
    UserResponse, UserUpdate, UserListResponse, UserCreate,
    LikeWorkoutRequest, LikedWorkoutResponse, LikedWorkoutListResponse,
    WorkoutLikeStatusResponse, BulkLikeCheckRequest, BulkLikeCheckResponse,
)
from uuid import UUID
from typing import Dict, Optional, List
import logging

from common.auth_guard import require_auth 

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/users", response_model = UserListResponse)
async def get_all_users(
    skip: int = 0,
    limit: int = 10,
    session: AsyncSession = Depends(get_session),
    token_payload: Dict = Depends(require_auth) 
):
    """Get all users with pagination"""
    try:
        users = await UserService.get_all_users(session, skip = skip, limit = limit)
        return UserListResponse(total = len(users), items = users)
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        raise HTTPException(status_code = 500, detail = "Failed to fetch users")



@router.get("/users/{uid}", response_model = UserResponse)
async def get_user(
    uid: UUID,
    session: AsyncSession = Depends(get_session),
    token_payload: Dict = Depends(require_auth)
):
    """Get user by UID"""
    try:
        user = await UserService.get_user_by_uid(session, uid)
        if not user:
            raise HTTPException(status_code = 404, detail = "User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user: {str(e)}")
        raise HTTPException(status_code = 500, detail = "Failed to fetch user")



@router.get("/users/auth0/{auth0_sub}", response_model = UserResponse)
async def get_user_by_auth0(
    auth0_sub: str,
    session: AsyncSession = Depends(get_session),
    token_payload: Dict = Depends(require_auth)
):
    """Get user by Auth0 sub"""
    try:
        user = await UserService.get_user_by_auth0_sub(session, auth0_sub)
        if not user:
            raise HTTPException(status_code = 404, detail = "User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user by auth0_sub: {str(e)}")
        raise HTTPException(status_code = 500, detail = "Failed to fetch user")



@router.post("/users", response_model = UserResponse)
async def create_user(
    user_create: UserCreate,
    session: AsyncSession = Depends(get_session),
    token_payload: Dict = Depends(require_auth) 
):
    """Create a new user"""
    try:
        user_data = user_create.model_dump()
        new_user = User(**user_data)
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        logger.info(f"Created user: {new_user.email}")
        return new_user
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        await session.rollback()
        raise HTTPException(status_code = 500, detail = "Failed to create user")



@router.post("/sync", response_model = UserResponse)
async def sync_user_from_auth(
    user_data: dict, 
    session: AsyncSession = Depends(get_session)
):
    """Sync user from Auth Service after Auth0 login"""
    try:
        auth0_sub = user_data.get("sub") or user_data.get("auth0_sub")
        
        if not auth0_sub:
            logger.error(f"Missing auth0_sub in user_data: {user_data}")
            raise HTTPException(status_code=400, detail="Missing auth0_sub (sub)")
        
        user = await UserService.get_or_create_user(
            session,
            auth0_sub,
            user_data
        )
        
        logger.info(f"Synced user: {user.email} (auth0_sub: {auth0_sub})")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))




@router.put("/users/{uid}", response_model = UserResponse)
async def update_user(
    uid: UUID,
    user_update: UserUpdate,
    session: AsyncSession = Depends(get_session),
    token_payload: Dict = Depends(require_auth) 
):
    """Update user"""
    try:
        update_data = user_update.model_dump(exclude_unset = True, mode = 'json')
        user = await UserService.update_user(session, uid, update_data)
        
        if not user:
            raise HTTPException(status_code = 404, detail = "User not found")
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(status_code = 500, detail = "Failed to update user")



@router.delete("/users/{uid}")
async def delete_user(
    uid: UUID,
    session: AsyncSession = Depends(get_session),
    token_payload: Dict = Depends(require_auth) 
):
    """Delete user"""
    try:
        success = await UserService.delete_user(session, uid)
        
        if not success:
            raise HTTPException(status_code = 404, detail = "User not found")
        
        return {"message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        raise HTTPException(status_code = 500, detail = "Failed to delete user")



@router.get("/users/search", response_model=UserListResponse)
async def search_users(
    q: str = Query(..., min_length=1, max_length=200, description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    session: AsyncSession = Depends(get_session),
    token_payload: Dict = Depends(require_auth)
):
    """Search users by username, email, first name, or last name"""
    try:
        users = await UserService.search_users(session, q, skip, limit)
        return UserListResponse(total=len(users), items=users)
    except Exception as e:
        logger.error(f"Error searching users: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search users")




@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "user-service"}



# =================== Liked Workouts =================== #

@router.post("/users/{uid}/liked-workouts", response_model=LikedWorkoutResponse, status_code=201)
async def like_workout(
    uid: UUID,
    request: LikeWorkoutRequest,
    session: AsyncSession = Depends(get_session),
    token_payload: Dict = Depends(require_auth)
):
    """Like a workout for a user"""
    try:
        success = await UserService.like_workout(session, uid, request.workout_id)
        if not success:
            raise HTTPException(status_code=409, detail="Workout already liked")

        workouts = await UserService.search_liked_workouts(
            session, uid, workout_ids=[request.workout_id]
        )
        if not workouts:
            raise HTTPException(status_code=500, detail="Failed to retrieve liked workout")

        return workouts[0]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error liking workout: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to like workout")


@router.delete("/users/{uid}/liked-workouts/{workout_id}", status_code=200)
async def unlike_workout(
    uid: UUID,
    workout_id: str,
    session: AsyncSession = Depends(get_session),
    token_payload: Dict = Depends(require_auth)
):
    """Unlike a workout for a user"""
    try:
        success = await UserService.unlike_workout(session, uid, workout_id)
        if not success:
            raise HTTPException(status_code=404, detail="Workout not liked")

        return {"message": "Workout unliked successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unliking workout: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to unlike workout")


@router.get("/users/{uid}/liked-workouts/check/{workout_id}", response_model=WorkoutLikeStatusResponse)
async def check_workout_liked(
    uid: UUID,
    workout_id: str,
    session: AsyncSession = Depends(get_session),
    token_payload: Dict = Depends(require_auth)
):
    """Check if a specific workout is liked by a user"""
    try:
        is_liked = await UserService.is_workout_liked(session, uid, workout_id)
        return WorkoutLikeStatusResponse(workout_id=workout_id, is_liked=is_liked)

    except Exception as e:
        logger.error(f"Error checking workout like status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to check like status")


@router.post("/users/{uid}/liked-workouts/check-bulk", response_model=BulkLikeCheckResponse)
async def check_workouts_liked_bulk(
    uid: UUID,
    request: BulkLikeCheckRequest,
    session: AsyncSession = Depends(get_session),
    token_payload: Dict = Depends(require_auth)
):
    """Check like status for multiple workouts at once"""
    try:
        results = {}
        for workout_id in request.workout_ids:
            results[workout_id] = await UserService.is_workout_liked(
                session, uid, workout_id
            )
        return BulkLikeCheckResponse(results=results)

    except Exception as e:
        logger.error(f"Error checking bulk workout like status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to check like statuses")


@router.get("/users/{uid}/liked-workouts", response_model=LikedWorkoutListResponse)
async def get_liked_workouts(
    uid: UUID,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max number of records to return"),
    session: AsyncSession = Depends(get_session),
    token_payload: Dict = Depends(require_auth)
):
    """Get all liked workouts for a user with pagination"""
    try:
        workouts = await UserService.get_liked_workouts(session, uid, skip, limit)
        total = await UserService.get_liked_workouts_count(session, uid)
        return LikedWorkoutListResponse(total=total, items=workouts)

    except Exception as e:
        logger.error(f"Error getting liked workouts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get liked workouts")


@router.get("/users/{uid}/liked-workouts/search", response_model=LikedWorkoutListResponse)
async def search_liked_workouts(
    uid: UUID,
    workout_ids: Optional[str] = Query(
        None,
        description="Comma-separated list of workout IDs to filter by"
    ),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max number of records to return"),
    session: AsyncSession = Depends(get_session),
    token_payload: Dict = Depends(require_auth)
):
    """Search and filter liked workouts for a user"""
    try:
        parsed_workout_ids = None
        if workout_ids:
            parsed_workout_ids = [wid.strip() for wid in workout_ids.split(",") if wid.strip()]

        workouts = await UserService.search_liked_workouts(
            session, uid, workout_ids=parsed_workout_ids, skip=skip, limit=limit
        )
        total = len(workouts)
        return LikedWorkoutListResponse(total=total, items=workouts)

    except Exception as e:
        logger.error(f"Error searching liked workouts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search liked workouts")