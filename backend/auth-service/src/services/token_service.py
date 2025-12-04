from src.services.redis_service import redis_service
from src.core.auth0 import auth0_manager
import logging
from typing import Optional, Dict
import uuid

logger = logging.getLogger(__name__)


class TokenService:
    """Service for managing tokens and refresh logic"""
    
    @staticmethod
    async def create_session(tokens: Dict, user_info: Dict) -> str:
        """Create session and return session_id"""
        try:
            session_id = str(uuid.uuid4())
            
            session_data = {
                "session_id": session_id,
                "access_token": tokens.get("access_token"),
                "refresh_token": tokens.get("refresh_token"),
                "id_token": tokens.get("id_token"),
                "token_type": tokens.get("token_type", "Bearer"),
                "expires_in": tokens.get("expires_in"),
                "user_id": user_info.get("sub"),
                "email": user_info.get("email"),
                "name": user_info.get("name"),
                "picture": user_info.get("picture"),
                "role": user_info.get("role", "user"),
                "internal_uid": user_info.get("internal_uid")
            }
            
            success = await redis_service.save_session(session_id, session_data)
            
            if success:
                logger.info(f"Created session {session_id} for user {user_info.get('email')}")
                return session_id
            else:
                logger.error("Failed to save session to Redis")
                return None
                
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            return None
    

    @staticmethod
    async def get_user_from_session(session_id: str) -> Optional[Dict]:
        """Get user info from session"""
        try:
            session = await redis_service.get_session(session_id)
            if session:
                await redis_service.refresh_session_expiry(session_id)
                return {
                    "user_id": session.get("user_id"),
                    "email": session.get("email"),
                    "name": session.get("name"),
                    "picture": session.get("picture"),
                    "role": session.get("role", "user"),
                    "internal_uid": session.get("internal_uid")
                }
            return None
        except Exception as e:
            logger.error(f"Error getting user from session: {str(e)}")
            return None
    

    @staticmethod
    async def refresh_access_token_for_session(session_id: str) -> Optional[str]:
        """Refresh access token for session"""
        try:
            session = await redis_service.get_session(session_id)
            if not session or not session.get("refresh_token"):
                logger.warning(f"No refresh token found for session {session_id}")
                return None
            
            new_tokens = await auth0_manager.refresh_access_token(
                session.get("refresh_token")
            )
            
            if new_tokens:
                session["access_token"] = new_tokens.get("access_token")
                session["expires_in"] = new_tokens.get("expires_in")
                
                await redis_service.save_session(session_id, session)
                logger.info(f"Refreshed access token for session {session_id}")
                return new_tokens.get("access_token")
            else:
                logger.error(f"Failed to refresh token for session {session_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error refreshing access token: {str(e)}")
            return None
    

    @staticmethod
    async def destroy_session(session_id: str) -> bool:
        """Destroy session"""
        try:
            success = await redis_service.delete_session(session_id)
            if success:
                logger.info(f"Destroyed session {session_id}")
            return success
        except Exception as e:
            logger.error(f"Error destroying session: {str(e)}")
            return False