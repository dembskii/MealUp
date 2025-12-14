from typing import Any, List, Optional
from datetime import datetime
import logging

from src.db.mongodb import get_database
from src.models.model import (
    Exercise, ExerciseCreate, ExerciseUpdate,
    BodyPart, Advancement, ExerciseCategory
)
from src.core.config import settings

logger = logging.getLogger(__name__)


class ExerciseService:
    """Service for exercise CRUD operations"""
    
    @staticmethod
    async def create_exercise(exercise_data: ExerciseCreate) -> Exercise:
        """Create a new exercise"""
        db = get_database()
        collection = db[settings.EXERCISES_COLLECTION]

        exercise = Exercise(
            name=exercise_data.name,
            body_part=exercise_data.body_part,
            advancement=exercise_data.advancement,
            category=exercise_data.category,
            description=exercise_data.description,
            hints=exercise_data.hints,
            image=exercise_data.image,
            video_url=exercise_data.video_url
        )

        exercise_dict = exercise.model_dump(by_alias=True)
        await collection.insert_one(exercise_dict)

        logger.info(f"Created exercise {exercise.id}: {exercise.name}")
        return exercise
    
    @staticmethod
    async def get_exercise(exercise_id: str) -> Optional[Exercise]:
        """Get an exercise by ID"""
        db = get_database()
        collection = db[settings.EXERCISES_COLLECTION]
        
        exercise_data = await collection.find_one({"_id": exercise_id})
        if exercise_data:
            return Exercise(**exercise_data)
        return None
    
    @staticmethod
    async def get_exercises(
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        body_part: Optional[BodyPart] = None,
        advancement: Optional[Advancement] = None,
        category: Optional[ExerciseCategory] = None
    ) -> List[Exercise]:
        """Get list of exercises with pagination and filters"""
        db = get_database()
        collection = db[settings.EXERCISES_COLLECTION]
        
        query: dict[str, Any] = {}
        
        if search:
            query["name"] = {"$regex": search, "$options": "i"}
        if body_part:
            query["body_part"] = body_part.value
        if advancement:
            query["advancement"] = advancement.value
        if category:
            query["category"] = category.value
        
        cursor = collection.find(query).sort("name", 1).skip(skip).limit(limit)
        exercises = await cursor.to_list(length=limit)

        return [Exercise(**exercise) for exercise in exercises]
    
    @staticmethod
    async def get_exercises_by_ids(exercise_ids: List[str]) -> List[Exercise]:
        """Get multiple exercises by their IDs"""
        db = get_database()
        collection = db[settings.EXERCISES_COLLECTION]
        
        cursor = collection.find({"_id": {"$in": exercise_ids}})
        exercises = await cursor.to_list(length=len(exercise_ids))
        
        return [Exercise(**exercise) for exercise in exercises]
    
    @staticmethod
    async def update_exercise(
        exercise_id: str,
        exercise_update: ExerciseUpdate
    ) -> Optional[Exercise]:
        """Update an exercise"""
        db = get_database()
        collection = db[settings.EXERCISES_COLLECTION]
        
        # Check if exercise exists
        existing = await collection.find_one({"_id": exercise_id})
        if not existing:
            return None
        
        # Prepare update data
        update_data = exercise_update.model_dump(exclude_unset=True)
        if update_data:
            update_data["_updated_at"] = datetime.utcnow()
            
            await collection.update_one(
                {"_id": exercise_id},
                {"$set": update_data}
            )
            
            updated_exercise = await collection.find_one({"_id": exercise_id})
            if updated_exercise is None:
                return None
            return Exercise(**updated_exercise)
        
        return Exercise(**existing)
    
    @staticmethod
    async def delete_exercise(exercise_id: str) -> bool:
        """Delete an exercise"""
        db = get_database()
        collection = db[settings.EXERCISES_COLLECTION]
        
        result = await collection.delete_one({"_id": exercise_id})
        
        if result.deleted_count > 0:
            logger.info(f"Deleted exercise {exercise_id}")
            return True
        return False
    
    @staticmethod
    async def count_exercises(
        body_part: Optional[BodyPart] = None,
        advancement: Optional[Advancement] = None,
        category: Optional[ExerciseCategory] = None
    ) -> int:
        """Count exercises with optional filters"""
        db = get_database()
        collection = db[settings.EXERCISES_COLLECTION]
        
        query: dict[str, Any] = {}
        
        if body_part:
            query["body_part"] = body_part.value
        if advancement:
            query["advancement"] = advancement.value
        if category:
            query["category"] = category.value
        
        count = await collection.count_documents(query)
        return count
