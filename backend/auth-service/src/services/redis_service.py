import redis.asyncio as redis
import json
import logging
from src.core.config import settings
from typing import Optional, Dict

logger = logging.getLogger(__name__)



class RedisService:
    """Service for managing Redis sessions"""
    
    def __init__(self):
        self.redis_url = settings.REDIS_AUTH_URL
        self.session_expiry = settings.SESSION_EXPIRY
        self.client: Optional[redis.Redis] = None
    

    async def connect(self):
        """Connect to Redis"""
        try:
            self.client = await redis.from_url(self.redis_url, decode_responses=True)
            await self.client.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise
    

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.client:
            await self.client.close()
            logger.info("Disconnected from Redis")
    

    async def save_session(self, session_id: str, session_data: Dict) -> bool:
        """Save session data to Redis"""
        try:
            session_json = json.dumps(session_data)
            await self.client.setex(
                f"session:{session_id}",
                self.session_expiry,
                session_json
            )
            logger.info(f"Saved session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving session: {str(e)}")
            return False
    

    async def get_session(self, session_id: str) -> Optional[Dict]:
        """Retrieve session data from Redis"""
        try:
            session_json = await self.client.get(f"session:{session_id}")
            if session_json:
                logger.info(f"Retrieved session {session_id}")
                return json.loads(session_json)
            else:
                logger.warning(f"Session {session_id} not found")
                return None
        except Exception as e:
            logger.error(f"Error retrieving session: {str(e)}")
            return None
    

    async def delete_session(self, session_id: str) -> bool:
        """Delete session from Redis"""
        try:
            await self.client.delete(f"session:{session_id}")
            logger.info(f"Deleted session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting session: {str(e)}")
            return False
    

    async def refresh_session_expiry(self, session_id: str) -> bool:
        """Refresh session expiry time"""
        try:
            await self.client.expire(f"session:{session_id}", self.session_expiry)
            logger.info(f"Refreshed expiry for session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error refreshing session expiry: {str(e)}")
            return False


redis_service = RedisService()