# backend/recipe-service/init_ingredients.py
"""
Script to initialize MongoDB with sample ingredients.
Run: python init_ingredients.py
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from db.mongodb import connect_to_mongodb, disconnect_from_mongodb, get_database
from core.config import settings
from models.model import Ingredient, Macro
import uuid

# Sample ingredients with macros
SAMPLE_INGREDIENTS = [
    {
        "name": "Tomato",
        "units": "g",
        "image": "https://via.placeholder.com/150?text=Tomato",
        "macro_per_hundred": {"calories": 18, "carbs": 3.9, "proteins": 0.9, "fats": 0.2}
    },
    {
        "name": "Chicken Breast",
        "units": "g",
        "image": "https://via.placeholder.com/150?text=Chicken",
        "macro_per_hundred": {"calories": 165, "carbs": 0, "proteins": 31, "fats": 3.6}
    },
    {
        "name": "Olive Oil",
        "units": "ml",
        "image": "https://via.placeholder.com/150?text=Oil",
        "macro_per_hundred": {"calories": 884, "carbs": 0, "proteins": 0, "fats": 100}
    },
    {
        "name": "Garlic",
        "units": "g",
        "image": "https://via.placeholder.com/150?text=Garlic",
        "macro_per_hundred": {"calories": 149, "carbs": 33.1, "proteins": 6.4, "fats": 0.5}
    },
    {
        "name": "Onion",
        "units": "g",
        "image": "https://via.placeholder.com/150?text=Onion",
        "macro_per_hundred": {"calories": 40, "carbs": 9, "proteins": 1.1, "fats": 0.1}
    },
    {
        "name": "Bell Pepper",
        "units": "g",
        "image": "https://via.placeholder.com/150?text=Pepper",
        "macro_per_hundred": {"calories": 31, "carbs": 5.8, "proteins": 0.9, "fats": 0.3}
    },
    {
        "name": "Salt",
        "units": "g",
        "image": "https://via.placeholder.com/150?text=Salt",
        "macro_per_hundred": {"calories": 0, "carbs": 0, "proteins": 0, "fats": 0}
    },
    {
        "name": "Black Pepper",
        "units": "g",
        "image": "https://via.placeholder.com/150?text=Pepper",
        "macro_per_hundred": {"calories": 251, "carbs": 64.8, "proteins": 10.4, "fats": 3.3}
    },
    {
        "name": "Basil",
        "units": "g",
        "image": "https://via.placeholder.com/150?text=Basil",
        "macro_per_hundred": {"calories": 27, "carbs": 3.2, "proteins": 3.2, "fats": 0.6}
    },
    {
        "name": "Mozzarella Cheese",
        "units": "g",
        "image": "https://via.placeholder.com/150?text=Cheese",
        "macro_per_hundred": {"calories": 280, "carbs": 3.1, "proteins": 28, "fats": 17}
    },
    {
        "name": "Rice",
        "units": "g",
        "image": "https://via.placeholder.com/150?text=Rice",
        "macro_per_hundred": {"calories": 130, "carbs": 28, "proteins": 2.7, "fats": 0.3}
    },
    {
        "name": "Pasta",
        "units": "g",
        "image": "https://via.placeholder.com/150?text=Pasta",
        "macro_per_hundred": {"calories": 131, "carbs": 25, "proteins": 5, "fats": 1.1}
    },
    {
        "name": "Carrots",
        "units": "g",
        "image": "https://via.placeholder.com/150?text=Carrot",
        "macro_per_hundred": {"calories": 41, "carbs": 9.6, "proteins": 0.9, "fats": 0.2}
    },
    {
        "name": "Spinach",
        "units": "g",
        "image": "https://via.placeholder.com/150?text=Spinach",
        "macro_per_hundred": {"calories": 23, "carbs": 3.6, "proteins": 2.9, "fats": 0.4}
    },
    {
        "name": "Broccoli",
        "units": "g",
        "image": "https://via.placeholder.com/150?text=Broccoli",
        "macro_per_hundred": {"calories": 34, "carbs": 7, "proteins": 2.8, "fats": 0.4}
    },
    {
        "name": "Lemon",
        "units": "ml",
        "image": "https://via.placeholder.com/150?text=Lemon",
        "macro_per_hundred": {"calories": 29, "carbs": 9.3, "proteins": 1.1, "fats": 0.3}
    },
    {
        "name": "Potato",
        "units": "g",
        "image": "https://via.placeholder.com/150?text=Potato",
        "macro_per_hundred": {"calories": 77, "carbs": 17, "proteins": 2, "fats": 0.1}
    },
    {
        "name": "Salmon",
        "units": "g",
        "image": "https://via.placeholder.com/150?text=Salmon",
        "macro_per_hundred": {"calories": 208, "carbs": 0, "proteins": 20, "fats": 13}
    },
    {
        "name": "Butter",
        "units": "g",
        "image": "https://via.placeholder.com/150?text=Butter",
        "macro_per_hundred": {"calories": 717, "carbs": 0.1, "proteins": 0.9, "fats": 81}
    },
    {
        "name": "Eggs",
        "units": "pcs",
        "image": "https://via.placeholder.com/150?text=Eggs",
        "macro_per_hundred": {"calories": 155, "carbs": 1.1, "proteins": 13, "fats": 11}
    },
]


async def init_ingredients():
    """Initialize ingredients collection with sample data"""
    try:
        print("Connecting to MongoDB...")
        await connect_to_mongodb()
        
        db = get_database()
        collection = db[settings.INGREDIENTS_COLLECTION]
        
        # Check if ingredients already exist
        existing_count = await collection.count_documents({})
        if existing_count > 0:
            print(f"⚠️  Collection already has {existing_count} ingredients.")
            print("Aborting initialization.")
            return
        
        # Insert sample ingredients
        ingredients_to_insert = []
        for data in SAMPLE_INGREDIENTS:
            ingredient = Ingredient(
                name=data["name"],
                units=data["units"],
                image=data["image"],
                macro_per_hundred=Macro(**data["macro_per_hundred"])
            )
            ingredients_to_insert.append(ingredient.model_dump(by_alias=True))
        
        result = await collection.insert_many(ingredients_to_insert)
        
        print(f"✅ Successfully initialized {len(result.inserted_ids)} ingredients!")
        print("\nSample ingredients added:")
        for ingredient_id, ingredient_data in zip(result.inserted_ids, SAMPLE_INGREDIENTS):
            print(f"  • {ingredient_data['name']} ({ingredient_id})")
        
        await disconnect_from_mongodb()
        
    except Exception as e:
        print(f"❌ Error initializing ingredients: {e}")
        await disconnect_from_mongodb()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(init_ingredients())