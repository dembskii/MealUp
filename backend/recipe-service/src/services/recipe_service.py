from typing import List, Optional
from datetime import datetime
from bson import ObjectId
import logging

from src.db.mongodb import get_database
from src.models.model import Recipe, RecipeCreate, RecipeUpdate
from src.core.config import settings

logger = logging.getLogger(__name__)


class RecipeService:
    """Service for recipe CRUD operations"""
    
    @staticmethod
    async def create_recipe(recipe_data: RecipeCreate, author_id: str) -> Recipe:
        """Create a new recipe"""
        db = get_database()
        collection = db[settings.RECIPES_COLLECTION]
        
        recipe = Recipe(
            author_id=author_id,
            ingredients=recipe_data.ingredients,
            prepare_instruction=recipe_data.prepare_instruction,
            time_to_prepare=recipe_data.time_to_prepare,
            images=recipe_data.images
        )
        
        recipe_dict = recipe.model_dump(by_alias=True)
        await collection.insert_one(recipe_dict)
        
        logger.info(f"Created recipe {recipe.id} by author {author_id}")
        return recipe
    
    @staticmethod
    async def get_recipe(recipe_id: str) -> Optional[Recipe]:
        """Get a recipe by ID"""
        db = get_database()
        collection = db[settings.RECIPES_COLLECTION]
        
        recipe_data = await collection.find_one({"_id": recipe_id})
        if recipe_data:
            return Recipe(**recipe_data)
        return None
    
    @staticmethod
    async def get_recipes(
        skip: int = 0,
        limit: int = 20,
        author_id: Optional[str] = None
    ) -> List[Recipe]:
        """Get list of recipes with pagination"""
        db = get_database()
        collection = db[settings.RECIPES_COLLECTION]
        
        query = {}
        if author_id:
            query["author_id"] = author_id
        
        cursor = collection.find(query).sort("_created_at", -1).skip(skip).limit(limit)
        recipes = await cursor.to_list(length=limit)
        
        return [Recipe(**recipe) for recipe in recipes]
    
    @staticmethod
    async def update_recipe(
        recipe_id: str,
        recipe_update: RecipeUpdate,
        author_id: str
    ) -> Optional[Recipe]:
        """Update a recipe (only by author)"""
        db = get_database()
        collection = db[settings.RECIPES_COLLECTION]
        
        # Check if recipe exists and belongs to author
        existing = await collection.find_one({"_id": recipe_id, "author_id": author_id})
        if not existing:
            return None
        
        # Prepare update data
        update_data = recipe_update.model_dump(exclude_unset=True)
        if update_data:
            update_data["_updated_at"] = datetime.utcnow()
            
            result = await collection.update_one(
                {"_id": recipe_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated recipe {recipe_id}")
                updated_recipe = await collection.find_one({"_id": recipe_id})
                return Recipe(**updated_recipe)
        
        return Recipe(**existing)
    
    @staticmethod
    async def delete_recipe(recipe_id: str, author_id: str) -> bool:
        """Delete a recipe (only by author)"""
        db = get_database()
        collection = db[settings.RECIPES_COLLECTION]
        
        result = await collection.delete_one({"_id": recipe_id, "author_id": author_id})
        
        if result.deleted_count > 0:
            logger.info(f"Deleted recipe {recipe_id}")
            return True
        return False
    
    @staticmethod
    async def like_recipe(recipe_id: str) -> Optional[Recipe]:
        """Increment like count for a recipe"""
        db = get_database()
        collection = db[settings.RECIPES_COLLECTION]
        
        result = await collection.update_one(
            {"_id": recipe_id},
            {"$inc": {"total_likes": 1}}
        )
        
        if result.modified_count > 0:
            logger.info(f"Liked recipe {recipe_id}")
            updated_recipe = await collection.find_one({"_id": recipe_id})
            return Recipe(**updated_recipe)
        return None
    
    @staticmethod
    async def unlike_recipe(recipe_id: str) -> Optional[Recipe]:
        """Decrement like count for a recipe"""
        db = get_database()
        collection = db[settings.RECIPES_COLLECTION]
        
        result = await collection.update_one(
            {"_id": recipe_id, "total_likes": {"$gt": 0}},
            {"$inc": {"total_likes": -1}}
        )
        
        if result.modified_count > 0:
            logger.info(f"Unliked recipe {recipe_id}")
            updated_recipe = await collection.find_one({"_id": recipe_id})
            return Recipe(**updated_recipe)
        return None