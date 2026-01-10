from typing import Any, List, Optional
from datetime import datetime
import logging

from src.db.mongodb import get_database
from src.models.model import (
    WorkoutPlan, WorkoutPlanCreate, WorkoutPlanUpdate, WorkoutPlanResponse,
    WorkoutPlanDetailed
)
from src.core.config import settings
from src.services.training_service import TrainingService

logger = logging.getLogger(__name__)


class WorkoutPlanService:
    """Service for workout plan CRUD operations"""
    
    @staticmethod
    async def create_workout_plan(
        trainer_id: str,
        plan_data: WorkoutPlanCreate
    ) -> WorkoutPlan:
        """Create a new workout plan"""
        db = get_database()
        collection = db[settings.WORKOUT_PLANS_COLLECTION]

        if plan_data.trainings:
            trainings = await TrainingService.get_trainings_by_ids(plan_data.trainings)
            if len(trainings) != len(plan_data.trainings):
                raise ValueError("One or more training IDs are invalid")

        workout_plan = WorkoutPlan(
            name=plan_data.name,
            trainer_id=trainer_id,
            clients=plan_data.clients or [],
            trainings=plan_data.trainings or [],
            description=plan_data.description,
            is_public=plan_data.is_public
        )

        plan_dict = workout_plan.model_dump(by_alias=True)
        await collection.insert_one(plan_dict)

        logger.info(f"Created workout plan {workout_plan.id}: {workout_plan.name} by trainer {trainer_id}")
        return workout_plan
    
    @staticmethod
    async def get_workout_plan(plan_id: str) -> Optional[WorkoutPlan]:
        """Get a workout plan by ID"""
        db = get_database()
        collection = db[settings.WORKOUT_PLANS_COLLECTION]
        
        plan_data = await collection.find_one({"_id": plan_id})
        if plan_data:
            return WorkoutPlan(**plan_data)
        return None
    
    @staticmethod
    async def get_workout_plans(
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        is_public: Optional[bool] = None,
        trainer_id: Optional[str] = None
    ) -> List[WorkoutPlan]:
        """Get list of workout plans with pagination and filters"""
        db = get_database()
        collection = db[settings.WORKOUT_PLANS_COLLECTION]
        
        query: dict[str, Any] = {}
        
        if search:
            query["name"] = {"$regex": search, "$options": "i"}
        if is_public is not None:
            query["is_public"] = is_public
        if trainer_id:
            query["trainer_id"] = trainer_id
        
        cursor = collection.find(query).sort("_created_at", -1).skip(skip).limit(limit)
        plans = await cursor.to_list(length=limit)

        return [WorkoutPlan(**plan) for plan in plans]
    
    @staticmethod
    async def get_workout_plans_by_ids(plan_ids: List[str]) -> List[WorkoutPlan]:
        """Get multiple workout plans by their IDs"""
        db = get_database()
        collection = db[settings.WORKOUT_PLANS_COLLECTION]
        
        cursor = collection.find({"_id": {"$in": plan_ids}})
        plans = await cursor.to_list(length=len(plan_ids))
        
        return [WorkoutPlan(**plan) for plan in plans]
    
    @staticmethod
    async def update_workout_plan(
        plan_id: str,
        plan_update: WorkoutPlanUpdate,
        trainer_id: Optional[str] = None
    ) -> Optional[WorkoutPlan]:
        """Update a workout plan (only by creator)"""
        db = get_database()
        collection = db[settings.WORKOUT_PLANS_COLLECTION]
        
        existing = await collection.find_one({"_id": plan_id})
        if not existing:
            return None
        
        if trainer_id and existing.get("trainer_id") != trainer_id:
            raise PermissionError("Only the plan creator can update it")
        
        if plan_update.trainings:
            trainings = await TrainingService.get_trainings_by_ids(plan_update.trainings)
            if len(trainings) != len(plan_update.trainings):
                raise ValueError("One or more training IDs are invalid")
        
        update_data = plan_update.model_dump(exclude_unset=True)
        if update_data:
            update_data["_updated_at"] = datetime.utcnow()
            
            await collection.update_one(
                {"_id": plan_id},
                {"$set": update_data}
            )
            
            updated_plan = await collection.find_one({"_id": plan_id})
            if updated_plan is None:
                return None
            return WorkoutPlan(**updated_plan)
        
        return WorkoutPlan(**existing)
    
    @staticmethod
    async def delete_workout_plan(
        plan_id: str,
        trainer_id: Optional[str] = None
    ) -> bool:
        """Delete a workout plan (only by creator)"""
        db = get_database()
        collection = db[settings.WORKOUT_PLANS_COLLECTION]
        
        existing = await collection.find_one({"_id": plan_id})
        if not existing:
            return False
        
        if trainer_id and existing.get("trainer_id") != trainer_id:
            raise PermissionError("Only the plan creator can delete it")
        
        result = await collection.delete_one({"_id": plan_id})
        
        if result.deleted_count > 0:
            logger.info(f"Deleted workout plan {plan_id}")
            return True
        return False
    
    @staticmethod
    async def add_client_to_plan(
        plan_id: str,
        client_id: str,
        trainer_id: Optional[str] = None
    ) -> Optional[WorkoutPlan]:
        """Add a client to a workout plan"""
        db = get_database()
        collection = db[settings.WORKOUT_PLANS_COLLECTION]
        
        existing = await collection.find_one({"_id": plan_id})
        if not existing:
            return None
        
        if trainer_id and existing.get("trainer_id") != trainer_id:
            raise PermissionError("Only the plan creator can add clients")
        
        if client_id not in existing.get("clients", []):
            await collection.update_one(
                {"_id": plan_id},
                {
                    "$push": {"clients": client_id},
                    "$set": {"_updated_at": datetime.utcnow()}
                }
            )
            logger.info(f"Added client {client_id} to plan {plan_id}")
        
        updated_plan = await collection.find_one({"_id": plan_id})
        return WorkoutPlan(**updated_plan) if updated_plan else None
    
    @staticmethod
    async def remove_client_from_plan(
        plan_id: str,
        client_id: str,
        trainer_id: Optional[str] = None
    ) -> Optional[WorkoutPlan]:
        """Remove a client from a workout plan"""
        db = get_database()
        collection = db[settings.WORKOUT_PLANS_COLLECTION]
        
        existing = await collection.find_one({"_id": plan_id})
        if not existing:
            return None
        
        if trainer_id and existing.get("trainer_id") != trainer_id:
            raise PermissionError("Only the plan creator can remove clients")
        
        await collection.update_one(
            {"_id": plan_id},
            {
                "$pull": {"clients": client_id},
                "$set": {"_updated_at": datetime.utcnow()}
            }
        )
        logger.info(f"Removed client {client_id} from plan {plan_id}")
        
        updated_plan = await collection.find_one({"_id": plan_id})
        return WorkoutPlan(**updated_plan) if updated_plan else None
    
    @staticmethod
    async def add_training_to_plan(
        plan_id: str,
        training_id: str,
        trainer_id: Optional[str] = None
    ) -> Optional[WorkoutPlan]:
        """Add a training session to a workout plan"""
        db = get_database()
        collection = db[settings.WORKOUT_PLANS_COLLECTION]
        
        existing = await collection.find_one({"_id": plan_id})
        if not existing:
            return None
        
        if trainer_id and existing.get("trainer_id") != trainer_id:
            raise PermissionError("Only the plan creator can add trainings")
        
        training = await TrainingService.get_training(training_id)
        if not training:
            raise ValueError("Training not found")
        
        if training_id not in existing.get("trainings", []):
            await collection.update_one(
                {"_id": plan_id},
                {
                    "$push": {"trainings": training_id},
                    "$set": {"_updated_at": datetime.utcnow()}
                }
            )
            logger.info(f"Added training {training_id} to plan {plan_id}")
        
        updated_plan = await collection.find_one({"_id": plan_id})
        return WorkoutPlan(**updated_plan) if updated_plan else None
    
    @staticmethod
    async def remove_training_from_plan(
        plan_id: str,
        training_id: str,
        trainer_id: Optional[str] = None
    ) -> Optional[WorkoutPlan]:
        """Remove a training session from a workout plan"""
        db = get_database()
        collection = db[settings.WORKOUT_PLANS_COLLECTION]
        
        existing = await collection.find_one({"_id": plan_id})
        if not existing:
            return None
        
        if trainer_id and existing.get("trainer_id") != trainer_id:
            raise PermissionError("Only the plan creator can remove trainings")
        
        await collection.update_one(
            {"_id": plan_id},
            {
                "$pull": {"trainings": training_id},
                "$set": {"_updated_at": datetime.utcnow()}
            }
        )
        logger.info(f"Removed training {training_id} from plan {plan_id}")
        
        updated_plan = await collection.find_one({"_id": plan_id})
        return WorkoutPlan(**updated_plan) if updated_plan else None
    
    @staticmethod
    async def like_workout_plan(plan_id: str) -> Optional[WorkoutPlan]:
        """Increment like count for a workout plan"""
        db = get_database()
        collection = db[settings.WORKOUT_PLANS_COLLECTION]
        
        result = await collection.find_one_and_update(
            {"_id": plan_id},
            {
                "$inc": {"total_likes": 1},
                "$set": {"_updated_at": datetime.utcnow()}
            },
            return_document=True
        )
        
        return WorkoutPlan(**result) if result else None
    
    @staticmethod
    async def unlike_workout_plan(plan_id: str) -> Optional[WorkoutPlan]:
        """Decrement like count for a workout plan"""
        db = get_database()
        collection = db[settings.WORKOUT_PLANS_COLLECTION]
        
        result = await collection.find_one_and_update(
            {"_id": plan_id},
            {
                "$inc": {"total_likes": -1},
                "$set": {"_updated_at": datetime.utcnow()}
            },
            return_document=True
        )
        
        return WorkoutPlan(**result) if result else None
    
    @staticmethod
    async def count_workout_plans(
        is_public: Optional[bool] = None,
        trainer_id: Optional[str] = None
    ) -> int:
        """Count workout plans with optional filters"""
        db = get_database()
        collection = db[settings.WORKOUT_PLANS_COLLECTION]
        
        query: dict[str, Any] = {}
        
        if is_public is not None:
            query["is_public"] = is_public
        if trainer_id:
            query["trainer_id"] = trainer_id
        
        count = await collection.count_documents(query)
        return count
    
    @staticmethod
    async def get_workout_plan_detailed(plan_id: str) -> Optional[WorkoutPlanDetailed]:
        """Get a workout plan with full training and exercise details"""
        db = get_database()
        
        plan = await WorkoutPlanService.get_workout_plan(plan_id)
        if not plan:
            return None
        
        trainings_with_exercises = await TrainingService.get_trainings_with_exercises(plan.trainings)
        
        return WorkoutPlanDetailed(
        **{
            "_id": plan.id,
            "name": plan.name,
            "trainer_id": plan.trainer_id,
            "clients": plan.clients,
            "trainings": trainings_with_exercises,
            "description": plan.description,
            "is_public": plan.is_public,
            "total_likes": plan.total_likes,
            "_created_at": plan.created_at,
            "_updated_at": plan.updated_at
            }
        )
    
    @staticmethod
    async def get_trainer_plans(trainer_id: str, skip: int = 0, limit: int = 100) -> List[WorkoutPlan]:
        """Get all workout plans created by a trainer"""
        return await WorkoutPlanService.get_workout_plans(
            skip=skip,
            limit=limit,
            trainer_id=trainer_id
        )
    
    @staticmethod
    async def get_client_plans(client_id: str, skip: int = 0, limit: int = 100) -> List[WorkoutPlan]:
        """Get all workout plans assigned to a client"""
        db = get_database()
        collection = db[settings.WORKOUT_PLANS_COLLECTION]
        
        query = {"clients": client_id}
        cursor = collection.find(query).sort("_created_at", -1).skip(skip).limit(limit)
        plans = await cursor.to_list(length=limit)
        
        return [WorkoutPlan(**plan) for plan in plans]
