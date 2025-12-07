from pymongo import MongoClient
from pymongo.database import Database
from contextlib import contextmanager
from typing import Optional
import logging

from src.core.config import settings

logger = logging.getLogger(__name__)

# Global MongoDB client and database instances
_client: Optional[MongoClient] = None
_database: Optional[Database] = None


async def connect_to_mongodb():
    """Connect to MongoDB (pymongo sync client)"""
    global _client, _database
    try:
        _client = MongoClient(settings.MONGODB_URL)
        _database = _client[settings.MONGODB_DB_NAME]

        # Verify connection
        _client.admin.command("ping")
        logger.info("Connected to MongoDB")

        # Create indexes
        _create_indexes()
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def disconnect_from_mongodb():
    """Disconnect from MongoDB"""
    global _client
    if _client:
        _client.close()
        logger.info("Disconnected from MongoDB")


def _create_indexes():
    """Create indexes for better query performance"""
    if _database is None:
        return

    try:
        # Exercises collection indexes
        exercises_collection = _database[settings.EXERCISES_COLLECTION]
        exercises_collection.create_index("name")
        exercises_collection.create_index("body_part")
        exercises_collection.create_index("advancement")
        exercises_collection.create_index("category")
        exercises_collection.create_index("_created_at")
        exercises_collection.create_index([("name", 1), ("body_part", 1)])

        # Trainings collection indexes
        trainings_collection = _database[settings.TRAININGS_COLLECTION]
        trainings_collection.create_index("day")
        trainings_collection.create_index("training_type")
        trainings_collection.create_index("_created_at")
        trainings_collection.create_index([("day", 1), ("training_type", 1)])

        # Workout plans collection indexes
        workout_plans_collection = _database[settings.WORKOUT_PLANS_COLLECTION]
        workout_plans_collection.create_index("trainer_id")
        workout_plans_collection.create_index("clients")
        workout_plans_collection.create_index("is_public")
        workout_plans_collection.create_index("_created_at")
        workout_plans_collection.create_index([("trainer_id", 1), ("_created_at", -1)])

        logger.info("✓ Database indexes created")
    except Exception as e:
        logger.error(f"✗ Failed to create indexes: {e}")


def get_database() -> Database:
    """Get the MongoDB database instance"""
    if _database is None:
        raise RuntimeError("Database not connected. Call connect_to_mongodb() first.")
    return _database


def get_client() -> MongoClient:
    """Get the MongoDB client instance"""
    if _client is None:
        raise RuntimeError("Client not connected. Call connect_to_mongodb() first.")
    return _client


@contextmanager
def get_session():
    """Get a MongoDB session for transactions"""
    client = get_client()
    with client.start_session() as session:
        yield session
