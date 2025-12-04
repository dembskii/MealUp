from fastapi import APIRouter, HTTPException, Depends, Cookie
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.main import get_session
from src.models.model import User
from src.services.user_service import UserService
from src.validators.schema import UserResponse, UserUpdate, UserListResponse, UserCreate
from typing import Optional
from uuid import UUID
import logging

logger = logging.getLogger(__name__)
router = APIRouter()



@router.get("/users", response_model = UserListResponse)
async def get_all_users(
    skip: int = 0,
    limit: int = 10,
    session: AsyncSession = Depends(get_session)
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
    session: AsyncSession = Depends(get_session)
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
    session: AsyncSession = Depends(get_session)
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
    session: AsyncSession = Depends(get_session)
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
    session: AsyncSession = Depends(get_session)
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
    session: AsyncSession = Depends(get_session)
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



@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "user-service"}