from typing import Any, List, Optional
from datetime import datetime
import logging

from src.db.mongodb import get_database
from src.models.model import (
    Recipe, RecipeCreate, RecipeUpdate, 
    Ingredient, IngredientCreate, IngredientUpdate
)
from src.core.config import settings

logger = logging.getLogger(__name__)


class IngredientService:
    """Service for ingredient CRUD operations"""
    
    @staticmethod
    async def create_ingredient(ingredient_data: IngredientCreate) -> Ingredient:
        """Create a new ingredient"""
        db = get_database()
        collection = db[settings.INGREDIENTS_COLLECTION]

        ingredient = Ingredient(
            name=ingredient_data.name,
            units=ingredient_data.units,
            image=ingredient_data.image,
            macro_per_hundred=ingredient_data.macro_per_hundred
        )

        ingredient_dict = ingredient.model_dump(by_alias=True)
        await collection.insert_one(ingredient_dict)

        logger.info(f"Created ingredient {ingredient.id}")
        return ingredient
    
    @staticmethod
    async def get_ingredient(ingredient_id: str) -> Optional[Ingredient]:
        """Get an ingredient by ID"""
        db = get_database()
        collection = db[settings.INGREDIENTS_COLLECTION]
        
        ingredient_data = await collection.find_one({"_id": ingredient_id})
        if ingredient_data:
            return Ingredient(**ingredient_data)
        return None
    
    @staticmethod
    async def get_ingredients(
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None
    ) -> List[Ingredient]:
        """Get list of ingredients with pagination and search"""
        db = get_database()
        collection = db[settings.INGREDIENTS_COLLECTION]
        
        query = {}
        if search:
            query["name"] = {"$regex": search, "$options": "i"}
        
        cursor = collection.find(query).sort("name", 1).skip(skip).limit(limit)
        ingredients = await cursor.to_list(length=limit)

        return [Ingredient(**ingredient) for ingredient in ingredients]
    
    @staticmethod
    async def update_ingredient(
        ingredient_id: str,
        ingredient_update: IngredientUpdate
    ) -> Optional[Ingredient]:
        """Update an ingredient"""
        db = get_database()
        collection = db[settings.INGREDIENTS_COLLECTION]
        
        # Check if ingredient exists
        existing = await collection.find_one({"_id": ingredient_id})
        if not existing:
            return None
        
        # Prepare update data
        update_data = ingredient_update.model_dump(exclude_unset=True)
        if update_data:
            update_data["_updated_at"] = datetime.utcnow()
            
            await collection.update_one(
                {"_id": ingredient_id},
                {"$set": update_data}
            )
            
            updated_ingredient = await collection.find_one({"_id": ingredient_id})
            if updated_ingredient is None:
                return None
            return Ingredient(**updated_ingredient)
        
        return Ingredient(**existing)
    
    @staticmethod
    async def delete_ingredient(ingredient_id: str) -> bool:
        """Delete an ingredient"""
        db = get_database()
        collection = db[settings.INGREDIENTS_COLLECTION]
        
        result = await collection.delete_one({"_id": ingredient_id})
        
        if result.deleted_count > 0:
            logger.info(f"Deleted ingredient {ingredient_id}")
            return True
        return False


class RecipeService:
    """Service for recipe CRUD operations"""
    
    @staticmethod
    async def create_recipe(recipe_data: RecipeCreate, author_id: str) -> Recipe:
        """Create a new recipe"""
        db = get_database()
        collection = db[settings.RECIPES_COLLECTION]

        recipe = Recipe(
            name=recipe_data.name,
            author_id=author_id,
            ingredients=recipe_data.ingredients,
            prepare_instruction=recipe_data.prepare_instruction,
            time_to_prepare=recipe_data.time_to_prepare,
            image=None,
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
                if updated_recipe is None:
                    return None
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
            if updated_recipe is None:
                return None
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
            if updated_recipe is None:
                return None
            return Recipe(**updated_recipe)
        return None


    @staticmethod
    async def search_recipes(
        query: str,
        tags: Optional[List[str]] = None,
        author_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Recipe]:
        """Search recipes with MongoDB text search and filters"""
        db = get_database()
        collection = db[settings.RECIPES_COLLECTION]
        
        filters: dict[str, Any] = {}
        
        # Text search using MongoDB regex
        if query:
            filters["$or"] = [
                {"name": {"$regex": query, "$options": "i"}},
                {"prepare_instruction": {"$regex": query, "$options": "i"}}
            ]
        
        # Filter by tags
        if tags:
            filters["tags"] = {"$in": tags}
        
        # Filter by author
        if author_id:
            filters["author_id"] = author_id
        
        cursor = collection.find(filters).sort("_created_at", -1).skip(skip).limit(limit)
        recipes = await cursor.to_list(length=limit)
        
        logger.info(f"Found {len(recipes)} recipes for query '{query}'")
        return [Recipe(**recipe) for recipe in recipes]