from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import logging

from src.core.config import settings

logger = logging.getLogger(__name__)

# Global MongoDB client and database instances
_client: Optional[AsyncIOMotorClient] = None
_database: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongodb():
    """Connect to MongoDB (motor async client)"""
    global _client, _database
    try:
        _client = AsyncIOMotorClient(settings.MONGODB_URL)
        _database = _client[settings.MONGODB_DB_NAME]

        # Verify connection
        await _client.admin.command("ping")
        logger.info("Connected to MongoDB")

        # Create indexes
        await _create_indexes()
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def disconnect_from_mongodb():
    """Disconnect from MongoDB"""
    global _client
    if _client:
        _client.close()
        logger.info("Disconnected from MongoDB")


async def _create_indexes():
    """Create indexes for better query performance"""
    if _database is None:
        return

    try:
        # Daily logs collection indexes
        daily_logs = _database[settings.DAILY_LOG_COLLECTION]
        await daily_logs.create_index("user_id")
        await daily_logs.create_index("date")
        await daily_logs.create_index([("user_id", 1), ("date", -1)])
        # Unique compound index: one daily log per user per date
        await daily_logs.create_index(
            [("user_id", 1), ("date", 1)],
            unique=True
        )

        # Meal entries collection indexes
        meal_entries = _database[settings.MEAL_ENTRIES_COLLECTION]
        await meal_entries.create_index("user_id")
        await meal_entries.create_index("daily_log_id")
        await meal_entries.create_index("date")
        await meal_entries.create_index([("user_id", 1), ("date", -1)])

        logger.info("✓ Database indexes created")
    except Exception as e:
        logger.error(f"✗ Failed to create indexes: {e}")


def get_database() -> AsyncIOMotorDatabase:
    """Get the MongoDB database instance"""
    if _database is None:
        raise RuntimeError("Database not connected. Call connect_to_mongodb() first.")
    return _database


def get_client() -> AsyncIOMotorClient:
    """Get the MongoDB client instance"""
    if _client is None:
        raise RuntimeError("Client not connected. Call connect_to_mongodb() first.")
    return _client
