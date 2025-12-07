from typing import Any, List, Optional
from datetime import datetime
import asyncio
import logging

from src.db.mongodb import get_database
from src.models.model import (
    WorkoutPlan, WorkoutPlanCreate, WorkoutPlanUpdate
)
from src.services.training_service import TrainingService
from src.core.config import settings

logger = logging.getLogger(__name__)


class WorkoutPlanService:
    """Service for workout plan CRUD operations"""
    
    @staticmethod
    async def create_workout_plan(
        plan_data: WorkoutPlanCreate, 
        trainer_id: str
    ) -> WorkoutPlan:
        """Create a new workout plan"""
        db = get_database()
        collection = db[settings.WORKOUT_PLANS_COLLECTION]

        workout_plan = WorkoutPlan(
            name=plan_data.name,
            trainer_id=trainer_id,
            clients=plan_data.clients or [],
            trainings=plan_data.trainings or [],
            description=plan_data.description,
            is_public=plan_data.is_public
        )

        plan_dict = workout_plan.model_dump(by_alias=True)
        await asyncio.to_thread(collection.insert_one, plan_dict)

        logger.info(f"Created workout plan {workout_plan.id}: {workout_plan.name} by trainer {trainer_id}")
        return workout_plan
    
    @staticmethod
    async def get_workout_plan(plan_id: str) -> Optional[WorkoutPlan]:
        """Get a workout plan by ID"""
        db = get_database()
        collection = db[settings.WORKOUT_PLANS_COLLECTION]
        
        plan_data: Optional[dict[str, Any]] = await asyncio.to_thread(
            collection.find_one, 
            {"_id": plan_id}
        )
        if plan_data:
            return WorkoutPlan(**plan_data)
        return None
    
    @staticmethod
    async def get_workout_plan_detailed(plan_id: str) -> Optional[dict]:
        """Get a workout plan with full training and exercise details"""
        plan = await WorkoutPlanService.get_workout_plan(plan_id)
        if not plan:
            return None
        
        # Fetch all trainings with their exercises
        trainings_detailed = []
        for training_id in plan.trainings:
            training_with_exercises = await TrainingService.get_training_with_exercises(training_id)
            if training_with_exercises:
                trainings_detailed.append(training_with_exercises)
        
        return {
            "_id": plan.id,
            "name": plan.name,
            "trainer_id": plan.trainer_id,
            "clients": plan.clients,
            "trainings": trainings_detailed,
            "description": plan.description,
            "is_public": plan.is_public,
            "total_likes": plan.total_likes,
            "_created_at": plan.created_at,
            "_updated_at": plan.updated_at
        }
    
    @staticmethod
    async def get_workout_plans(
        skip: int = 0,
        limit: int = 20,
        trainer_id: Optional[str] = None,
        is_public: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[WorkoutPlan]:
        """Get list of workout plans with pagination and filters"""
        db = get_database()
        collection = db[settings.WORKOUT_PLANS_COLLECTION]
        
        query: dict[str, Any] = {}
        
        if trainer_id:
            query["trainer_id"] = trainer_id
        if is_public is not None:
            query["is_public"] = is_public
        if search:
            query["name"] = {"$regex": search, "$options": "i"}
        
        cursor = collection.find(query).sort("_created_at", -1).skip(skip).limit(limit)
        plans: list[dict[str, Any]] = await asyncio.to_thread(lambda: list(cursor))

        return [WorkoutPlan(**plan) for plan in plans]
    
    @staticmethod
    async def get_plans_for_client(
        client_id: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[WorkoutPlan]:
        """Get workout plans assigned to a specific client"""
        db = get_database()
        collection = db[settings.WORKOUT_PLANS_COLLECTION]
        
        cursor = collection.find({"clients": client_id}).sort("_created_at", -1).skip(skip).limit(limit)
        plans: list[dict[str, Any]] = await asyncio.to_thread(lambda: list(cursor))
        
        return [WorkoutPlan(**plan) for plan in plans]
    
    @staticmethod
    async def update_workout_plan(
        plan_id: str,
        plan_update: WorkoutPlanUpdate,
        trainer_id: str
    ) -> Optional[WorkoutPlan]:
        """Update a workout plan (only by trainer)"""
        db = get_database()
        collection = db[settings.WORKOUT_PLANS_COLLECTION]
        
        # Check if plan exists and belongs to trainer
        existing: Optional[dict[str, Any]] = await asyncio.to_thread(
            collection.find_one,
            {"_id": plan_id, "trainer_id": trainer_id}
        )
        if not existing:
            return None
        
        # Prepare update data
        update_data = plan_update.model_dump(exclude_unset=True)
        if update_data:
            update_data["_updated_at"] = datetime.utcnow()
            
            await asyncio.to_thread(
                collection.update_one,
                {"_id": plan_id},
                {"$set": update_data}
            )
            
            updated_plan: Optional[dict[str, Any]] = await asyncio.to_thread(
                collection.find_one,
                {"_id": plan_id}
            )
            if updated_plan is None:
                return None
            return WorkoutPlan(**updated_plan)
        
        return WorkoutPlan(**existing)
    
    @staticmethod
    async def delete_workout_plan(plan_id: str, trainer_id: str) -> bool:
        """Delete a workout plan (only by trainer)"""
        db = get_database()
        collection = db[settings.WORKOUT_PLANS_COLLECTION]
        
        result = await asyncio.to_thread(
            collection.delete_one, 
            {"_id": plan_id, "trainer_id": trainer_id}
        )
        
        if result.deleted_count > 0:
            logger.info(f"Deleted workout plan {plan_id}")
            return True
        return False
    
    @staticmethod
    async def add_training_to_plan(
        plan_id: str,
        training_id: str,
        trainer_id: str
    ) -> Optional[WorkoutPlan]:
        """Add a training session to a workout plan"""
        db = get_database()
        collection = db[settings.WORKOUT_PLANS_COLLECTION]
        
        result = await asyncio.to_thread(
            collection.update_one,
            {"_id": plan_id, "trainer_id": trainer_id},
            {
                "$addToSet": {"trainings": training_id},
                "$set": {"_updated_at": datetime.utcnow()}
            }
        )
        
        if result.modified_count > 0 or result.matched_count > 0:
            return await WorkoutPlanService.get_workout_plan(plan_id)
        return None
    
    @staticmethod
    async def remove_training_from_plan(
        plan_id: str,
        training_id: str,
        trainer_id: str
    ) -> Optional[WorkoutPlan]:
        """Remove a training session from a workout plan"""
        db = get_database()
        collection = db[settings.WORKOUT_PLANS_COLLECTION]
        
        result = await asyncio.to_thread(
            collection.update_one,
            {"_id": plan_id, "trainer_id": trainer_id},
            {
                "$pull": {"trainings": training_id},
                "$set": {"_updated_at": datetime.utcnow()}
            }
        )
        
        if result.modified_count > 0:
            return await WorkoutPlanService.get_workout_plan(plan_id)
        return None
    
    @staticmethod
    async def add_client_to_plan(
        plan_id: str,
        client_id: str,
        trainer_id: str
    ) -> Optional[WorkoutPlan]:
        """Add a client to a workout plan"""
        db = get_database()
        collection = db[settings.WORKOUT_PLANS_COLLECTION]
        
        result = await asyncio.to_thread(
            collection.update_one,
            {"_id": plan_id, "trainer_id": trainer_id},
            {
                "$addToSet": {"clients": client_id},
                "$set": {"_updated_at": datetime.utcnow()}
            }
        )
        
        if result.modified_count > 0 or result.matched_count > 0:
            return await WorkoutPlanService.get_workout_plan(plan_id)
        return None
    
    @staticmethod
    async def remove_client_from_plan(
        plan_id: str,
        client_id: str,
        trainer_id: str
    ) -> Optional[WorkoutPlan]:
        """Remove a client from a workout plan"""
        db = get_database()
        collection = db[settings.WORKOUT_PLANS_COLLECTION]
        
        result = await asyncio.to_thread(
            collection.update_one,
            {"_id": plan_id, "trainer_id": trainer_id},
            {
                "$pull": {"clients": client_id},
                "$set": {"_updated_at": datetime.utcnow()}
            }
        )
        
        if result.modified_count > 0:
            return await WorkoutPlanService.get_workout_plan(plan_id)
        return None
    
    @staticmethod
    async def like_workout_plan(plan_id: str) -> Optional[WorkoutPlan]:
        """Like a workout plan (increment like count)"""
        db = get_database()
        collection = db[settings.WORKOUT_PLANS_COLLECTION]
        
        result = await asyncio.to_thread(
            collection.update_one,
            {"_id": plan_id},
            {
                "$inc": {"total_likes": 1},
                "$set": {"_updated_at": datetime.utcnow()}
            }
        )
        
        if result.modified_count > 0:
            return await WorkoutPlanService.get_workout_plan(plan_id)
        return None
    
    @staticmethod
    async def unlike_workout_plan(plan_id: str) -> Optional[WorkoutPlan]:
        """Unlike a workout plan (decrement like count, min 0)"""
        db = get_database()
        collection = db[settings.WORKOUT_PLANS_COLLECTION]
        
        # First check current likes
        plan = await WorkoutPlanService.get_workout_plan(plan_id)
        if not plan or plan.total_likes <= 0:
            return plan
        
        result = await asyncio.to_thread(
            collection.update_one,
            {"_id": plan_id, "total_likes": {"$gt": 0}},
            {
                "$inc": {"total_likes": -1},
                "$set": {"_updated_at": datetime.utcnow()}
            }
        )
        
        if result.modified_count > 0:
            return await WorkoutPlanService.get_workout_plan(plan_id)
        return plan
    
    @staticmethod
    async def count_workout_plans(
        trainer_id: Optional[str] = None,
        is_public: Optional[bool] = None
    ) -> int:
        """Count workout plans with optional filters"""
        db = get_database()
        collection = db[settings.WORKOUT_PLANS_COLLECTION]
        
        query: dict[str, Any] = {}
        
        if trainer_id:
            query["trainer_id"] = trainer_id
        if is_public is not None:
            query["is_public"] = is_public
        
        count: int = await asyncio.to_thread(collection.count_documents, query)
        return count
