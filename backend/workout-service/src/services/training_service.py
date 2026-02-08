from typing import Any, List, Optional
from datetime import datetime
import logging

from src.db.mongodb import get_database
from src.models.model import (
    Training, TrainingCreate, TrainingUpdate, TrainingResponse,
    TrainingType, TrainingWithExercises
)
from src.core.config import settings
from src.services.exercise_service import ExerciseService

logger = logging.getLogger(__name__)


class TrainingService:
    """Service for training session CRUD operations"""
    
    @staticmethod
    async def create_training(training_data: TrainingCreate) -> Training:
        """Create a new training session"""
        db = get_database()
        collection = db[settings.TRAININGS_COLLECTION]

        exercise_ids = [ex.exercise_id for ex in training_data.exercises]
        exercises = await ExerciseService.get_exercises_by_ids(exercise_ids)
        if len(exercises) != len(exercise_ids):
            raise ValueError("One or more exercise IDs are invalid")

        training = Training(
            name=training_data.name,
            exercises=training_data.exercises,
            est_time=training_data.est_time,
            training_type=training_data.training_type,
            description=training_data.description
        )

        training_dict = training.model_dump(by_alias=True)
        await collection.insert_one(training_dict)

        logger.info(f"Created training {training.id}: {training.name}")
        return training
    
    @staticmethod
    async def get_training(training_id: str) -> Optional[Training]:
        """Get a training session by ID"""
        db = get_database()
        collection = db[settings.TRAININGS_COLLECTION]
        
        training_data = await collection.find_one({"_id": training_id})
        if training_data:
            return Training(**training_data)
        return None
    
    @staticmethod
    async def get_trainings(
        skip: int = 0,
        limit: int = 100,
        training_type: Optional[TrainingType] = None,
        search: Optional[str] = None
    ) -> List[Training]:
        """Get list of training sessions with pagination and filters"""
        db = get_database()
        collection = db[settings.TRAININGS_COLLECTION]
        
        query: dict[str, Any] = {}
        
        if training_type:
            query["training_type"] = training_type.value
        if search:
            query["name"] = {"$regex": search, "$options": "i"}
        
        cursor = collection.find(query).sort("name", 1).skip(skip).limit(limit)
        trainings = await cursor.to_list(length=limit)

        return [Training(**training) for training in trainings]
    
    @staticmethod
    async def get_trainings_by_ids(training_ids: List[str]) -> List[Training]:
        """Get multiple training sessions by their IDs"""
        db = get_database()
        collection = db[settings.TRAININGS_COLLECTION]
        
        cursor = collection.find({"_id": {"$in": training_ids}})
        trainings = await cursor.to_list(length=len(training_ids))
        
        return [Training(**training) for training in trainings]
    
    @staticmethod
    async def update_training(
        training_id: str,
        training_update: TrainingUpdate
    ) -> Optional[Training]:
        """Update a training session"""
        db = get_database()
        collection = db[settings.TRAININGS_COLLECTION]
        
        existing = await collection.find_one({"_id": training_id})
        if not existing:
            return None
        
        if training_update.exercises:
            exercise_ids = [ex.exercise_id for ex in training_update.exercises]
            exercises = await ExerciseService.get_exercises_by_ids(exercise_ids)
            if len(exercises) != len(exercise_ids):
                raise ValueError("One or more exercise IDs are invalid")
        

        update_data = training_update.model_dump(exclude_unset=True)
        if update_data:
            update_data["_updated_at"] = datetime.utcnow()
            
            await collection.update_one(
                {"_id": training_id},
                {"$set": update_data}
            )
            
            updated_training = await collection.find_one({"_id": training_id})
            if updated_training is None:
                return None
            return Training(**updated_training)
        
        return Training(**existing)
    
    @staticmethod
    async def delete_training(training_id: str) -> bool:
        """Delete a training session"""
        db = get_database()
        collection = db[settings.TRAININGS_COLLECTION]
        
        result = await collection.delete_one({"_id": training_id})
        
        if result.deleted_count > 0:
            logger.info(f"Deleted training {training_id}")
            return True
        return False
    
    @staticmethod
    async def count_trainings(
        training_type: Optional[TrainingType] = None
    ) -> int:
        """Count training sessions with optional filters"""
        db = get_database()
        collection = db[settings.TRAININGS_COLLECTION]
        
        query: dict[str, Any] = {}
        
        if training_type:
            query["training_type"] = training_type.value
        
        count = await collection.count_documents(query)
        return count
    
    @staticmethod
    async def get_training_with_exercises(training_id: str) -> Optional[TrainingWithExercises]:
        """Get a training session with full exercise details"""
        db = get_database()
        trainings_collection = db[settings.TRAININGS_COLLECTION]
        exercises_collection = db[settings.EXERCISES_COLLECTION]
        
        training_data = await trainings_collection.find_one({"_id": training_id})
        if not training_data:
            return None
        
        enriched_exercises = []
        for training_exercise in training_data.get("exercises", []):
            exercise_id = training_exercise.get("exercise_id")
            exercise_data = await exercises_collection.find_one({"_id": exercise_id})
            
            if exercise_data:
                enriched_exercises.append({
                    **training_exercise,
                    "exercise_details": exercise_data
                })
            else:
                enriched_exercises.append(training_exercise)
        
        training_data["exercises"] = enriched_exercises
        return TrainingWithExercises(**training_data)
    
    @staticmethod
    async def get_trainings_with_exercises(training_ids: List[str]) -> List[TrainingWithExercises]:
        """Get multiple training sessions with full exercise details"""
        db = get_database()
        trainings_collection = db[settings.TRAININGS_COLLECTION]
        exercises_collection = db[settings.EXERCISES_COLLECTION]
        
        result = []
        for training_id in training_ids:
            training_with_exercises = await TrainingService.get_training_with_exercises(training_id)
            if training_with_exercises:
                result.append(training_with_exercises)
        
        return result
