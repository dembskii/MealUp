from typing import Any, List, Optional
from datetime import datetime
import asyncio
import logging

from src.db.mongodb import get_database
from src.models.model import (
    Training, TrainingCreate, TrainingUpdate,
    DayOfWeek, TrainingType, TrainingWithExercises
)
from src.services.exercise_service import ExerciseService
from src.core.config import settings

logger = logging.getLogger(__name__)


class TrainingService:
    """Service for training session CRUD operations"""
    
    @staticmethod
    async def create_training(training_data: TrainingCreate) -> Training:
        """Create a new training session"""
        db = get_database()
        collection = db[settings.TRAININGS_COLLECTION]

        training = Training(
            name=training_data.name,
            exercises=training_data.exercises,
            est_time=training_data.est_time,
            day=training_data.day,
            training_type=training_data.training_type,
            description=training_data.description
        )

        training_dict = training.model_dump(by_alias=True)
        await asyncio.to_thread(collection.insert_one, training_dict)

        logger.info(f"Created training {training.id}: {training.name}")
        return training
    
    @staticmethod
    async def get_training(training_id: str) -> Optional[Training]:
        """Get a training session by ID"""
        db = get_database()
        collection = db[settings.TRAININGS_COLLECTION]
        
        training_data: Optional[dict[str, Any]] = await asyncio.to_thread(
            collection.find_one, 
            {"_id": training_id}
        )
        if training_data:
            return Training(**training_data)
        return None
    
    @staticmethod
    async def get_training_with_exercises(training_id: str) -> Optional[dict]:
        """Get a training session with full exercise details"""
        training = await TrainingService.get_training(training_id)
        if not training:
            return None
        
        # Get all exercise IDs from the training
        exercise_ids = [ex.exercise_id for ex in training.exercises]
        
        # Fetch all exercises
        exercises = await ExerciseService.get_exercises_by_ids(exercise_ids)
        exercises_map = {ex.id: ex for ex in exercises}
        
        # Build enriched exercises list
        enriched_exercises = []
        for training_ex in training.exercises:
            exercise = exercises_map.get(training_ex.exercise_id)
            enriched_exercises.append({
                "exercise": exercise.model_dump(by_alias=True) if exercise else None,
                "sets": [s.model_dump() for s in training_ex.sets],
                "rest_between_sets": training_ex.rest_between_sets,
                "notes": training_ex.notes
            })
        
        return {
            "_id": training.id,
            "name": training.name,
            "exercises": enriched_exercises,
            "est_time": training.est_time,
            "day": training.day,
            "training_type": training.training_type,
            "description": training.description,
            "_created_at": training.created_at,
            "_updated_at": training.updated_at
        }
    
    @staticmethod
    async def get_trainings(
        skip: int = 0,
        limit: int = 50,
        day: Optional[DayOfWeek] = None,
        training_type: Optional[TrainingType] = None,
        search: Optional[str] = None
    ) -> List[Training]:
        """Get list of training sessions with pagination and filters"""
        db = get_database()
        collection = db[settings.TRAININGS_COLLECTION]
        
        query: dict[str, Any] = {}
        
        if day:
            query["day"] = day.value
        if training_type:
            query["training_type"] = training_type.value
        if search:
            query["name"] = {"$regex": search, "$options": "i"}
        
        cursor = collection.find(query).sort("_created_at", -1).skip(skip).limit(limit)
        trainings: list[dict[str, Any]] = await asyncio.to_thread(lambda: list(cursor))

        return [Training(**training) for training in trainings]
    
    @staticmethod
    async def get_trainings_by_ids(training_ids: List[str]) -> List[Training]:
        """Get multiple training sessions by their IDs"""
        db = get_database()
        collection = db[settings.TRAININGS_COLLECTION]
        
        cursor = collection.find({"_id": {"$in": training_ids}})
        trainings: list[dict[str, Any]] = await asyncio.to_thread(lambda: list(cursor))
        
        return [Training(**training) for training in trainings]
    
    @staticmethod
    async def update_training(
        training_id: str,
        training_update: TrainingUpdate
    ) -> Optional[Training]:
        """Update a training session"""
        db = get_database()
        collection = db[settings.TRAININGS_COLLECTION]
        
        # Check if training exists
        existing: Optional[dict[str, Any]] = await asyncio.to_thread(
            collection.find_one,
            {"_id": training_id}
        )
        if not existing:
            return None
        
        # Prepare update data
        update_data = training_update.model_dump(exclude_unset=True)
        if update_data:
            # Convert exercises to dict if present
            if "exercises" in update_data and update_data["exercises"]:
                update_data["exercises"] = [
                    ex.model_dump() if hasattr(ex, 'model_dump') else ex 
                    for ex in update_data["exercises"]
                ]
            
            update_data["_updated_at"] = datetime.utcnow()
            
            await asyncio.to_thread(
                collection.update_one,
                {"_id": training_id},
                {"$set": update_data}
            )
            
            updated_training: Optional[dict[str, Any]] = await asyncio.to_thread(
                collection.find_one,
                {"_id": training_id}
            )
            if updated_training is None:
                return None
            return Training(**updated_training)
        
        return Training(**existing)
    
    @staticmethod
    async def delete_training(training_id: str) -> bool:
        """Delete a training session"""
        db = get_database()
        collection = db[settings.TRAININGS_COLLECTION]
        
        result = await asyncio.to_thread(
            collection.delete_one, 
            {"_id": training_id}
        )
        
        if result.deleted_count > 0:
            logger.info(f"Deleted training {training_id}")
            return True
        return False
    
    @staticmethod
    async def add_exercise_to_training(
        training_id: str,
        exercise_id: str,
        sets: List[dict],
        rest_between_sets: int = 60,
        notes: Optional[str] = None
    ) -> Optional[Training]:
        """Add an exercise to an existing training session"""
        db = get_database()
        collection = db[settings.TRAININGS_COLLECTION]
        
        new_exercise = {
            "exercise_id": exercise_id,
            "sets": sets,
            "rest_between_sets": rest_between_sets,
            "notes": notes
        }
        
        result = await asyncio.to_thread(
            collection.update_one,
            {"_id": training_id},
            {
                "$push": {"exercises": new_exercise},
                "$set": {"_updated_at": datetime.utcnow()}
            }
        )
        
        if result.modified_count > 0:
            return await TrainingService.get_training(training_id)
        return None
    
    @staticmethod
    async def remove_exercise_from_training(
        training_id: str,
        exercise_id: str
    ) -> Optional[Training]:
        """Remove an exercise from a training session"""
        db = get_database()
        collection = db[settings.TRAININGS_COLLECTION]
        
        result = await asyncio.to_thread(
            collection.update_one,
            {"_id": training_id},
            {
                "$pull": {"exercises": {"exercise_id": exercise_id}},
                "$set": {"_updated_at": datetime.utcnow()}
            }
        )
        
        if result.modified_count > 0:
            return await TrainingService.get_training(training_id)
        return None
    
    @staticmethod
    async def count_trainings(
        day: Optional[DayOfWeek] = None,
        training_type: Optional[TrainingType] = None
    ) -> int:
        """Count training sessions with optional filters"""
        db = get_database()
        collection = db[settings.TRAININGS_COLLECTION]
        
        query: dict[str, Any] = {}
        
        if day:
            query["day"] = day.value
        if training_type:
            query["training_type"] = training_type.value
        
        count: int = await asyncio.to_thread(collection.count_documents, query)
        return count
