from typing import List, Optional
from datetime import datetime
import logging

from src.db.mongodb import get_database
from src.models.model import (
    DailyLog, DailyGoalsUpdate,
    MealEntry, MealEntryCreate, MealEntryUpdate,
    MacroNutrients, MealIngredient,
)
from src.core.config import settings

logger = logging.getLogger(__name__)


def _compute_meal_macros(ingredients: list) -> MacroNutrients:
    """Sum macros across all ingredients of a meal."""
    total = MacroNutrients()
    for ing in ingredients:
        macros = ing.macros if isinstance(ing, MealIngredient) else MacroNutrients(**ing.macros.model_dump())
        total.calories += macros.calories
        total.proteins += macros.proteins
        total.carbs += macros.carbs
        total.fats += macros.fats
    # Round to 2 decimal places
    total.calories = round(total.calories, 2)
    total.proteins = round(total.proteins, 2)
    total.carbs = round(total.carbs, 2)
    total.fats = round(total.fats, 2)
    return total


class DailyLogService:
    """Service for daily nutrition log operations"""

    @staticmethod
    async def get_or_create_daily_log(user_id: str, date: str) -> DailyLog:
        """Get existing daily log or create a new one for the given date."""
        db = get_database()
        collection = db[settings.DAILY_LOG_COLLECTION]

        existing = await collection.find_one({"user_id": user_id, "date": date})
        if existing:
            return DailyLog(**existing)

        daily_log = DailyLog(user_id=user_id, date=date)
        log_dict = daily_log.model_dump(by_alias=True)
        await collection.insert_one(log_dict)
        logger.info(f"Created daily log {daily_log.id} for user {user_id} on {date}")
        return daily_log

    @staticmethod
    async def get_daily_log(user_id: str, date: str) -> Optional[DailyLog]:
        """Get a daily log by user and date."""
        db = get_database()
        collection = db[settings.DAILY_LOG_COLLECTION]

        log_data = await collection.find_one({"user_id": user_id, "date": date})
        if log_data:
            return DailyLog(**log_data)
        return None

    @staticmethod
    async def get_daily_logs_range(
        user_id: str,
        date_from: str,
        date_to: str
    ) -> List[DailyLog]:
        """Get daily logs for a user within a date range."""
        db = get_database()
        collection = db[settings.DAILY_LOG_COLLECTION]

        query = {
            "user_id": user_id,
            "date": {"$gte": date_from, "$lte": date_to}
        }
        cursor = collection.find(query).sort("date", -1)
        logs = await cursor.to_list(length=365)
        return [DailyLog(**log) for log in logs]

    @staticmethod
    async def update_goals(user_id: str, date: str, goals: DailyGoalsUpdate) -> Optional[DailyLog]:
        """Update daily nutrition goals."""
        db = get_database()
        collection = db[settings.DAILY_LOG_COLLECTION]

        # Ensure log exists
        await DailyLogService.get_or_create_daily_log(user_id, date)

        update_data = goals.model_dump(exclude_unset=True)
        if update_data:
            update_data["_updated_at"] = datetime.utcnow()
            await collection.update_one(
                {"user_id": user_id, "date": date},
                {"$set": update_data}
            )

        updated = await collection.find_one({"user_id": user_id, "date": date})
        if updated:
            return DailyLog(**updated)
        return None

    @staticmethod
    async def recalculate_daily_totals(user_id: str, date: str) -> None:
        """Recalculate totals in the daily log based on all meal entries."""
        db = get_database()
        daily_col = db[settings.DAILY_LOG_COLLECTION]
        meals_col = db[settings.MEAL_ENTRIES_COLLECTION]

        cursor = meals_col.find({"user_id": user_id, "date": date})
        meals = await cursor.to_list(length=100)

        total = MacroNutrients()
        for meal in meals:
            m = meal.get("total_macros", {})
            total.calories += m.get("calories", 0)
            total.proteins += m.get("proteins", 0)
            total.carbs += m.get("carbs", 0)
            total.fats += m.get("fats", 0)

        total.calories = round(total.calories, 2)
        total.proteins = round(total.proteins, 2)
        total.carbs = round(total.carbs, 2)
        total.fats = round(total.fats, 2)

        await daily_col.update_one(
            {"user_id": user_id, "date": date},
            {"$set": {
                "total_macros": total.model_dump(),
                "_updated_at": datetime.utcnow()
            }}
        )
        logger.info(f"Recalculated daily totals for user {user_id} on {date}")


class MealEntryService:
    """Service for meal entry CRUD operations"""

    @staticmethod
    async def create_meal_entry(data: MealEntryCreate, user_id: str) -> MealEntry:
        """Create a new meal entry and update daily log totals."""
        db = get_database()
        collection = db[settings.MEAL_ENTRIES_COLLECTION]

        # Ensure daily log exists
        daily_log = await DailyLogService.get_or_create_daily_log(user_id, data.date)

        # Build ingredient list with computed macros
        ingredients = [
            MealIngredient(
                ingredient_id=ing.ingredient_id,
                name=ing.name,
                quantity=ing.quantity,
                macros=ing.macros
            )
            for ing in data.ingredients
        ]

        total_macros = _compute_meal_macros(ingredients)

        entry = MealEntry(
            user_id=user_id,
            daily_log_id=daily_log.id,
            date=data.date,
            meal_type=data.meal_type,
            ingredients=ingredients,
            recipe_id=data.recipe_id,
            recipe_name=data.recipe_name,
            total_macros=total_macros,
            note=data.note,
        )

        entry_dict = entry.model_dump(by_alias=True)
        await collection.insert_one(entry_dict)

        # Recalculate daily totals
        await DailyLogService.recalculate_daily_totals(user_id, data.date)

        logger.info(f"Created meal entry {entry.id} ({data.meal_type}) for user {user_id}")
        return entry

    @staticmethod
    async def get_meal_entry(entry_id: str, user_id: str) -> Optional[MealEntry]:
        """Get a meal entry by ID (only if it belongs to this user)."""
        db = get_database()
        collection = db[settings.MEAL_ENTRIES_COLLECTION]

        data = await collection.find_one({"_id": entry_id, "user_id": user_id})
        if data:
            return MealEntry(**data)
        return None

    @staticmethod
    async def get_meals_for_date(user_id: str, date: str) -> List[MealEntry]:
        """Get all meal entries for a user on a given date."""
        db = get_database()
        collection = db[settings.MEAL_ENTRIES_COLLECTION]

        cursor = collection.find({"user_id": user_id, "date": date}).sort("_created_at", 1)
        meals = await cursor.to_list(length=50)
        return [MealEntry(**meal) for meal in meals]

    @staticmethod
    async def update_meal_entry(
        entry_id: str,
        update_data: MealEntryUpdate,
        user_id: str
    ) -> Optional[MealEntry]:
        """Update a meal entry and recalculate totals."""
        db = get_database()
        collection = db[settings.MEAL_ENTRIES_COLLECTION]

        existing = await collection.find_one({"_id": entry_id, "user_id": user_id})
        if not existing:
            return None

        updates = update_data.model_dump(exclude_unset=True)

        # If ingredients changed, recompute total macros
        if "ingredients" in updates:
            ingredients = [
                MealIngredient(
                    ingredient_id=ing["ingredient_id"],
                    name=ing["name"],
                    quantity=ing["quantity"],
                    macros=MacroNutrients(**ing["macros"])
                )
                for ing in updates["ingredients"]
            ]
            updates["total_macros"] = _compute_meal_macros(ingredients).model_dump()
            updates["ingredients"] = [ing.model_dump() for ing in ingredients]

        if updates:
            updates["_updated_at"] = datetime.utcnow()
            await collection.update_one({"_id": entry_id}, {"$set": updates})

            # Recalculate daily totals
            await DailyLogService.recalculate_daily_totals(user_id, existing["date"])

            updated = await collection.find_one({"_id": entry_id})
            if updated:
                return MealEntry(**updated)

        return MealEntry(**existing)

    @staticmethod
    async def delete_meal_entry(entry_id: str, user_id: str) -> bool:
        """Delete a meal entry and recalculate daily totals."""
        db = get_database()
        collection = db[settings.MEAL_ENTRIES_COLLECTION]

        existing = await collection.find_one({"_id": entry_id, "user_id": user_id})
        if not existing:
            return False

        result = await collection.delete_one({"_id": entry_id, "user_id": user_id})
        if result.deleted_count > 0:
            await DailyLogService.recalculate_daily_totals(user_id, existing["date"])
            logger.info(f"Deleted meal entry {entry_id}")
            return True
        return False
