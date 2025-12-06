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
        # Recipes collection indexes
        recipes_collection = _database[settings.RECIPES_COLLECTION]
        recipes_collection.create_index("author_id")
        recipes_collection.create_index("_created_at")
        recipes_collection.create_index("_updated_at")
        recipes_collection.create_index([("_created_at", -1)])

        # Ingredients collection indexes
        ingredients_collection = _database[settings.INGREDIENTS_COLLECTION]
        ingredients_collection.create_index("name")
        ingredients_collection.create_index("_created_at")

        # Recipe versions collection indexes (for versioning)
        versions_collection = _database[settings.RECIPE_VERSIONS_COLLECTION]
        versions_collection.create_index("recipe_id")
        versions_collection.create_index([("recipe_id", 1), ("version", -1)])

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