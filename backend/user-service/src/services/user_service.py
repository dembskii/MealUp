from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.models.model import User, UserRole
from typing import Optional, List
from uuid import UUID
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
                logger.info(f"Updated user: {existing_user.email}")
                return existing_user
            
            username = user_data.get("email", "").split("@")[0]
            new_user = User(
                auth0_sub=auth0_sub,
                email=user_data.get("email"),
                username=username,
                first_name=user_data.get("given_name", "First Name"),
                last_name=user_data.get("family_name", "Last Name"),
                role=UserRole.USER
            )
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            logger.info(f"Created new user: {new_user.email}")
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
        try:
            statement = select(User).where(User.uid == uid)
            result = await session.exec(statement)
            user = result.first()
            
            if not user:
                return None
            
            for key, value in user_data.items():
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