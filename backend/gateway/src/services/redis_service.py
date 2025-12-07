import redis.asyncio as redis
import json
import logging
from typing import Optional
from src.core.config import settings

logger = logging.getLogger(__name__)

class RedisService:
    def __init__(self):
        self.redis_url = settings.REDIS_AUTH_URL
        self.redis: Optional[redis.Redis] = None


    async def connect(self):
        try:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
            logger.info("Gateway connected to Auth Redis")
        except Exception as e:
            logger.error(f"Gateway failed to connect to Redis: {e}")


    async def close(self):
        if self.redis:
            await self.redis.close()
            logger.info("Gateway disconnected from Redis")


    async def get_token(self, session_id: str) -> Optional[str]:
        if not self.redis:
            logger.warning("Redis client is not initialized")
            return None

        try:
            data = await self.redis.get(f"session:{session_id}")
            
            if data:
                session_data = json.loads(data)
                return session_data.get("access_token")
            
            return None
        except Exception as e:
            logger.error(f"Error retrieving token from Redis: {e}")
            return None

    async def get_session(self, session_id: str) -> Optional[dict]:
        """Get full session data from Redis"""
        if not self.redis:
            logger.warning("Redis client is not initialized")
            return None

        try:
            data = await self.redis.get(f"session:{session_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error retrieving session from Redis: {e}")
            return None


redis_service = RedisService()