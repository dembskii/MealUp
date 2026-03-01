from typing import List, Optional
from datetime import datetime
import logging

from src.db.mongodb import get_database
from src.models.meal_entry import MealEntry, MacroNutrients, MealIngredient
from src.models.daily_log import DailyLog
from src.validators.meal_entry import MealEntryCreate, MealEntryUpdate
from src.validators.daily_log import DailyGoalsUpdate

from src.services.recipe_client import (
    fetch_recipe,
    fetch_ingredient,
    fetch_ingredients_bulk,
    convert_to_grams,
)

from src.core.config import settings

logger = logging.getLogger(__name__)


# ── Macro helpers ──────────────────────────────────────────────────────

def _compute_macros_for_quantity(macro_per_hundred: dict, quantity_grams: float) -> MacroNutrients:
    """Scale macro_per_hundred (recipe-service format) to actual quantity in grams."""
    factor = quantity_grams / 100.0
    return MacroNutrients(
        calories=round(macro_per_hundred.get("calories", 0) * factor, 2),
        proteins=round(macro_per_hundred.get("proteins", 0) * factor, 2),
        carbs=round(macro_per_hundred.get("carbs", 0) * factor, 2),
        fats=round(macro_per_hundred.get("fats", 0) * factor, 2),
    )


def _compute_meal_macros(ingredients: list) -> MacroNutrients:
    """Sum macros across all ingredients of a meal."""
    total = MacroNutrients()
    for ing in ingredients:
        macros = ing.macros if isinstance(ing, MealIngredient) else MacroNutrients(**ing.macros.model_dump())
        total.calories += macros.calories
        total.proteins += macros.proteins
        total.carbs += macros.carbs
        total.fats += macros.fats
    total.calories = round(total.calories, 2)
    total.proteins = round(total.proteins, 2)
    total.carbs = round(total.carbs, 2)
    total.fats = round(total.fats, 2)
    return total


# ── Recipe resolution ──────────────────────────────────────────────────

async def _resolve_ingredients_from_recipe(recipe_id: str) -> tuple[List[MealIngredient], str]:
    """Fetch a recipe from recipe-service, resolve every ingredient's macros.

    Returns (list_of_MealIngredient, recipe_name).
    Raises ValueError when recipe or critical ingredient data is missing.
    """
    recipe_data = await fetch_recipe(recipe_id)
    if not recipe_data:
        raise ValueError(f"Recipe {recipe_id} not found in recipe-service")

    recipe_name = recipe_data.get("name", "Unknown recipe")
    weighted_ingredients = recipe_data.get("ingredients", [])

    if not weighted_ingredients:
        raise ValueError(f"Recipe {recipe_id} has no ingredients")

    # Collect all ingredient IDs and fetch in bulk
    ing_ids = [wi["ingredient_id"] for wi in weighted_ingredients]
    ingredients_map = await fetch_ingredients_bulk(ing_ids)

    resolved: List[MealIngredient] = []
    for wi in weighted_ingredients:
        ing_id = wi["ingredient_id"]
        quantity_raw = wi.get("quantity", 0)
        unit = wi.get("capacity", "g")

        quantity_grams = convert_to_grams(quantity_raw, unit)

        ing_data = ingredients_map.get(ing_id)
        if not ing_data:
            logger.warning("Ingredient %s not found, skipping", ing_id)
            continue

        name = ing_data.get("name", "Unknown")
        macro_per_hundred = ing_data.get("macro_per_hundred")

        if macro_per_hundred:
            macros = _compute_macros_for_quantity(macro_per_hundred, quantity_grams)
        else:
            macros = MacroNutrients()
            logger.warning("Ingredient %s (%s) has no macro data", ing_id, name)

        resolved.append(MealIngredient(
            ingredient_id=ing_id,
            name=name,
            quantity=quantity_grams,
            macros=macros,
        ))

    return resolved, recipe_name


async def _resolve_manual_ingredients(
    raw_ingredients: list,
) -> List[MealIngredient]:
    """Resolve macros for manually-provided ingredients.

    For each ingredient the client sends ``ingredient_id`` + ``quantity``.
    We fetch ``macro_per_hundred`` from recipe-service and compute macros.
    If the client already supplied macros we use them as-is (trust mode).
    """
    ing_ids = [ing.ingredient_id for ing in raw_ingredients]
    ingredients_map = await fetch_ingredients_bulk(ing_ids)

    resolved: List[MealIngredient] = []
    for ing in raw_ingredients:
        # If client sent pre-computed macros AND name, trust them
        if ing.macros is not None and ing.name is not None:
            resolved.append(MealIngredient(
                ingredient_id=ing.ingredient_id,
                name=ing.name,
                quantity=ing.quantity,
                macros=ing.macros,
            ))
            continue

        # Otherwise resolve from recipe-service
        ing_data = ingredients_map.get(ing.ingredient_id)
        if not ing_data:
            logger.warning("Ingredient %s not found, skipping", ing.ingredient_id)
            continue

        name = ing.name or ing_data.get("name", "Unknown")
        macro_per_hundred = ing_data.get("macro_per_hundred")

        if macro_per_hundred:
            macros = _compute_macros_for_quantity(macro_per_hundred, ing.quantity)
        else:
            macros = MacroNutrients()
            logger.warning("Ingredient %s (%s) has no macro data", ing.ingredient_id, name)

        resolved.append(MealIngredient(
            ingredient_id=ing.ingredient_id,
            name=name,
            quantity=ing.quantity,
            macros=macros,
        ))

    return resolved


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
        """Create a new meal entry and update daily log totals.

        Resolves ingredients & macros from recipe-service:
        - If ``recipe_id`` is provided → fetch the recipe, resolve all ingredients.
        - If ``ingredients`` are provided → resolve macros per ingredient_id.
        - At least one of the two must be present.
        """
        db = get_database()
        collection = db[settings.MEAL_ENTRIES_COLLECTION]

        if not data.recipe_id and not data.ingredients:
            raise ValueError("Either recipe_id or ingredients must be provided")

        # Ensure daily log exists
        daily_log = await DailyLogService.get_or_create_daily_log(user_id, data.date)

        recipe_name = data.recipe_name

        # ── Resolve ingredients ───────────────────────────────────
        if data.recipe_id:
            # Mode 1: recipe-based — auto-resolve from recipe-service
            ingredients, resolved_name = await _resolve_ingredients_from_recipe(data.recipe_id)
            if not recipe_name:
                recipe_name = resolved_name
        else:
            # Mode 2: manual ingredients — resolve macros from recipe-service
            ingredients = await _resolve_manual_ingredients(data.ingredients)

        total_macros = _compute_meal_macros(ingredients)

        entry = MealEntry(
            user_id=user_id,
            daily_log_id=daily_log.id,
            date=data.date,
            meal_type=data.meal_type,
            ingredients=ingredients,
            recipe_id=data.recipe_id,
            recipe_name=recipe_name,
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
        """Update a meal entry and recalculate totals.

        If a new recipe_id is provided, re-resolves ingredients from recipe-service.
        If new ingredients are provided, re-resolves their macros.
        """
        db = get_database()
        collection = db[settings.MEAL_ENTRIES_COLLECTION]

        existing = await collection.find_one({"_id": entry_id, "user_id": user_id})
        if not existing:
            return None

        updates = update_data.model_dump(exclude_unset=True)

        # If recipe_id changed, re-resolve everything from recipe-service
        if "recipe_id" in updates and updates["recipe_id"]:
            ingredients, resolved_name = await _resolve_ingredients_from_recipe(updates["recipe_id"])
            updates["ingredients"] = [ing.model_dump() for ing in ingredients]
            updates["total_macros"] = _compute_meal_macros(ingredients).model_dump()
            if not updates.get("recipe_name"):
                updates["recipe_name"] = resolved_name

        # If only ingredients changed (no new recipe_id), resolve macros per ingredient
        elif "ingredients" in updates:
            from src.validators.meal_entry import MealIngredientCreate
            raw = [MealIngredientCreate(**ing) for ing in updates["ingredients"]]
            resolved = await _resolve_manual_ingredients(raw)
            updates["total_macros"] = _compute_meal_macros(resolved).model_dump()
            updates["ingredients"] = [ing.model_dump() for ing in resolved]

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
