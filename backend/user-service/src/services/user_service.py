from sqlmodel import select, or_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import func
from src.models.model import User, UserRole, LikedWorkout
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class UserService:
    """Service for managing users and Auth0 integration"""
    
    @staticmethod
    async def get_or_create_user(
        session: AsyncSession,
        auth0_sub: str,
        user_data: dict
    ) -> User:
        """Get existing user or create new one based on Auth0 sub"""
        try:
            statement = select(User).where(User.auth0_sub == auth0_sub)
            result = await session.exec(statement)
            existing_user = result.first()
            
            if existing_user:
                existing_user.email = user_data.get("email", existing_user.email)
                existing_user.first_name = user_data.get("given_name", existing_user.first_name)
                existing_user.last_name = user_data.get("family_name", existing_user.last_name)
                
                session.add(existing_user)
                await session.commit()
                await session.refresh(existing_user)
                logger.info(f"Updated user: {existing_user.email} (role unchanged: {existing_user.role})")
                return existing_user
            
            role_str = user_data.get("role", "user")
            try:
                role = UserRole(role_str)
            except ValueError:
                role = UserRole.USER
                logger.warning(f"Invalid role '{role_str}', defaulting to 'user'")
            
            username = user_data.get("email", "").split("@")[0]
            new_user = User(
                auth0_sub=auth0_sub,
                email=user_data.get("email"),
                username=username,
                first_name=user_data.get("given_name", "First Name"),
                last_name=user_data.get("family_name", "Last Name"),
                role=role
            )
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            logger.info(f"Created new user: {new_user.email} with role: {role}")
            return new_user
            
        except Exception as e:
            logger.error(f"Error in get_or_create_user: {str(e)}")
            await session.rollback()
            raise


    @staticmethod
    async def get_user_by_auth0_sub(session: AsyncSession, auth0_sub: str) -> Optional[User]:
        """Get user by Auth0 sub"""
        try:
            statement = select(User).where(User.auth0_sub == auth0_sub)
            result = await session.exec(statement)
            return result.first()
        except Exception as e:
            logger.error(f"Error getting user by auth0_sub: {str(e)}")
            return None


    @staticmethod
    async def get_user_by_uid(session: AsyncSession, uid: UUID) -> Optional[User]:
        """Get user by uid"""
        try:
            statement = select(User).where(User.uid == uid)
            result = await session.exec(statement)
            return result.first()
        except Exception as e:
            logger.error(f"Error getting user by uid: {str(e)}")
            return None


    @staticmethod
    async def get_all_users(session: AsyncSession, skip: int = 0, limit: int = 10) -> List[User]:
        """Get all users with pagination"""
        try:
            statement = select(User).offset(skip).limit(limit)
            result = await session.exec(statement)
            return result.all()
        except Exception as e:
            logger.error(f"Error getting all users: {str(e)}")
            return []


    @staticmethod
    async def update_user(session: AsyncSession, uid: UUID, user_data: dict) -> Optional[User]:
        """Update user"""
        PROTECTED_FIELDS = {"email", "auth0_sub", "uid", "created_at"}

        try:
            statement = select(User).where(User.uid == uid)
            result = await session.exec(statement)
            user = result.first()
        except Exception as e:
            logger.error(f"Database error while fetching user: {str(e)}")
            return None

        if not user:
            return None
            
        try:
            for key, value in user_data.items():
                if key in PROTECTED_FIELDS:
                    continue
                if value is not None and hasattr(user, key):
                    setattr(user, key, value)
            
            session.add(user)
            await session.commit()
            await session.refresh(user)
            logger.info(f"Updated user: {uid}")
            return user
        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
            await session.rollback()
            return None


    @staticmethod
    async def delete_user(session: AsyncSession, uid: UUID) -> bool:
        """Delete user"""
        try:
            statement = select(User).where(User.uid == uid)
            result = await session.exec(statement)
            user = result.first()
            
            if not user:
                return False
            
            await session.delete(user)
            await session.commit()
            logger.info(f"Deleted user: {uid}")
            return True
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            await session.rollback()
            return False


    @staticmethod
    async def search_users(
        session: AsyncSession,
        query: str,
        skip: int = 0,
        limit: int = 10
    ) -> List[User]:
        """Search users using PostgreSQL ILIKE"""
        try:
            like_query = f"%{query}%"
            
            statement = select(User).where(
                or_(
                    User.username.ilike(like_query),
                    User.email.ilike(like_query),
                    User.first_name.ilike(like_query),
                    User.last_name.ilike(like_query)
                )
            ).offset(skip).limit(limit)
            
            result = await session.exec(statement)
            users = result.all()
            
            logger.info(f"Found {len(users)} users matching query '{query}'")
            return users
            
        except Exception as e:
            logger.error(f"Error searching users: {str(e)}")
            return []


    # =================== Liked Workouts =================== #

    @staticmethod
    async def like_workout(
        session: AsyncSession,
        user_id: UUID,
        workout_id: str
    ) -> bool:
        """Like a workout. Returns False if already liked."""
        try:
            statement = select(LikedWorkout).where(
                LikedWorkout.user_id == user_id,
                LikedWorkout.workout_id == workout_id
            )
            result = await session.exec(statement)
            existing = result.first()

            if existing:
                logger.info(f"User {user_id} already liked workout {workout_id}")
                return False

            like = LikedWorkout(
                user_id=user_id,
                workout_id=workout_id,
                created_at=datetime.now(timezone.utc)
            )
            session.add(like)
            await session.commit()

            logger.info(f"User {user_id} liked workout {workout_id}")
            return True

        except Exception as e:
            logger.error(f"Error liking workout: {str(e)}")
            await session.rollback()
            return False

    @staticmethod
    async def unlike_workout(
        session: AsyncSession,
        user_id: UUID,
        workout_id: str
    ) -> bool:
        """Unlike a workout. Returns False if not liked."""
        try:
            statement = select(LikedWorkout).where(
                LikedWorkout.user_id == user_id,
                LikedWorkout.workout_id == workout_id
            )
            result = await session.exec(statement)
            existing = result.first()

            if not existing:
                logger.info(f"User {user_id} has not liked workout {workout_id}")
                return False

            await session.delete(existing)
            await session.commit()

            logger.info(f"User {user_id} unliked workout {workout_id}")
            return True

        except Exception as e:
            logger.error(f"Error unliking workout: {str(e)}")
            await session.rollback()
            return False

    @staticmethod
    async def is_workout_liked(
        session: AsyncSession,
        user_id: UUID,
        workout_id: str
    ) -> bool:
        """Check if a workout is liked by a user."""
        try:
            statement = select(LikedWorkout).where(
                LikedWorkout.user_id == user_id,
                LikedWorkout.workout_id == workout_id
            )
            result = await session.exec(statement)
            return result.first() is not None

        except Exception as e:
            logger.error(f"Error checking liked workout: {str(e)}")
            return False

    @staticmethod
    async def get_liked_workouts(
        session: AsyncSession,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20
    ) -> List[LikedWorkout]:
        """Get all liked workouts for a user with pagination."""
        try:
            statement = (
                select(LikedWorkout)
                .where(LikedWorkout.user_id == user_id)
                .order_by(LikedWorkout.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            result = await session.exec(statement)
            return result.all()

        except Exception as e:
            logger.error(f"Error getting liked workouts: {str(e)}")
            return []

    @staticmethod
    async def get_liked_workouts_count(
        session: AsyncSession,
        user_id: UUID
    ) -> int:
        """Get total count of liked workouts for a user."""
        try:
            statement = select(func.count(LikedWorkout.id)).where(
                LikedWorkout.user_id == user_id
            )
            result = await session.exec(statement)
            return result.first() or 0

        except Exception as e:
            logger.error(f"Error counting liked workouts: {str(e)}")
            return 0

    @staticmethod
    async def search_liked_workouts(
        session: AsyncSession,
        user_id: UUID,
        workout_ids: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[LikedWorkout]:
        """Search/filter liked workouts for a user.

        Args:
            workout_ids: Optional list of workout IDs to filter by
        """
        try:
            statement = select(LikedWorkout).where(
                LikedWorkout.user_id == user_id
            )

            if workout_ids:
                statement = statement.where(
                    LikedWorkout.workout_id.in_(workout_ids)
                )

            statement = (
                statement
                .order_by(LikedWorkout.created_at.desc())
                .offset(skip)
                .limit(limit)
            )

            result = await session.exec(statement)
            return result.all()

        except Exception as e:
            logger.error(f"Error searching liked workouts: {str(e)}")
            return []