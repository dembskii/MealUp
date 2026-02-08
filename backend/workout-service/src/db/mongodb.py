from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from contextlib import asynccontextmanager
from typing import Optional
import logging

from src.core.config import settings

logger = logging.getLogger(__name__)

# Global MongoDB client and database instances
_client: Optional[AsyncIOMotorClient] = None
_database: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongodb():
    """Connect to MongoDB using Motor async driver"""
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

        exercises_collection = _database[settings.EXERCISES_COLLECTION]
        await exercises_collection.create_index("name")
        await exercises_collection.create_index("body_part")
        await exercises_collection.create_index("advancement")
        await exercises_collection.create_index("category")
        await exercises_collection.create_index("_created_at")
        await exercises_collection.create_index([("name", 1), ("body_part", 1)])

        trainings_collection = _database[settings.TRAININGS_COLLECTION]
        await trainings_collection.create_index("training_type")
        await trainings_collection.create_index("_created_at")

        workout_plans_collection = _database[settings.WORKOUT_PLANS_COLLECTION]
        await workout_plans_collection.create_index("trainer_id")
        await workout_plans_collection.create_index("clients")
        await workout_plans_collection.create_index("is_public")
        await workout_plans_collection.create_index("_created_at")
        await workout_plans_collection.create_index([("trainer_id", 1), ("_created_at", -1)])

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


@asynccontextmanager
async def get_session():
    """Get a MongoDB session for transactions"""
    client = get_client()
    async with await client.start_session() as session:
        yield session
