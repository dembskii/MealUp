# backend/recipe-service/src/init_ingredients.py
"""
Initialize MongoDB with 300+ real-world ingredients.
Deterministic UUIDs are generated from ingredient names so that
init_recipes.py can reference them reliably.

Run from the src/ directory:
    python init_ingredients.py
"""

import asyncio
import sys
import uuid
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from db.mongodb import connect_to_mongodb, disconnect_from_mongodb, get_database
from core.config import settings
from models.model import Ingredient, Macro

# ---------------------------------------------------------------------------
# Deterministic ID generation — shared with init_recipes.py
# ---------------------------------------------------------------------------
INGREDIENT_NS = uuid.UUID("a3bb189e-8bf9-3888-9912-ace4e6543002")


def make_ingredient_id(name: str) -> str:
    """Generate a deterministic UUID-5 from an ingredient name."""
    return str(uuid.uuid5(INGREDIENT_NS, name.lower().strip()))


# ---------------------------------------------------------------------------
# Ingredient data — (name, units, cal, carbs, protein, fat) per 100 g/ml
# ---------------------------------------------------------------------------

VEGETABLES = [
    ("Tomato", "g", 18, 3.9, 0.9, 0.2),
    ("Cherry Tomato", "g", 18, 3.9, 0.9, 0.2),
    ("Roma Tomato", "g", 18, 3.5, 0.9, 0.2),
    ("Sun-Dried Tomato", "g", 258, 55.8, 14.1, 3.0),
    ("Canned Tomatoes", "g", 32, 5.6, 1.6, 0.6),
    ("Onion", "g", 40, 9.3, 1.1, 0.1),
    ("Red Onion", "g", 40, 9.3, 1.1, 0.1),
    ("Shallot", "g", 72, 16.8, 2.5, 0.1),
    ("Green Onion", "g", 32, 7.3, 1.8, 0.2),
    ("Leek", "g", 61, 14.2, 1.5, 0.3),
    ("Garlic", "g", 149, 33.1, 6.4, 0.5),
    ("Ginger", "g", 80, 17.8, 1.8, 0.8),
    ("Potato", "g", 77, 17.5, 2.0, 0.1),
    ("Sweet Potato", "g", 86, 20.1, 1.6, 0.1),
    ("Carrot", "g", 41, 9.6, 0.9, 0.2),
    ("Celery", "g", 16, 3.0, 0.7, 0.2),
    ("Celeriac", "g", 42, 9.2, 1.5, 0.3),
    ("Bell Pepper Red", "g", 31, 6.0, 1.0, 0.3),
    ("Bell Pepper Green", "g", 20, 4.6, 0.9, 0.2),
    ("Bell Pepper Yellow", "g", 27, 6.3, 1.0, 0.2),
    ("Jalapeno Pepper", "g", 29, 6.5, 0.9, 0.4),
    ("Chili Pepper", "g", 40, 8.8, 1.9, 0.4),
    ("Broccoli", "g", 34, 6.6, 2.8, 0.4),
    ("Cauliflower", "g", 25, 5.0, 1.9, 0.3),
    ("Cabbage", "g", 25, 5.8, 1.3, 0.1),
    ("Red Cabbage", "g", 31, 7.4, 1.4, 0.2),
    ("Brussels Sprouts", "g", 43, 9.0, 3.4, 0.3),
    ("Kale", "g", 49, 8.8, 4.3, 0.9),
    ("Spinach", "g", 23, 3.6, 2.9, 0.4),
    ("Swiss Chard", "g", 19, 3.7, 1.8, 0.2),
    ("Arugula", "g", 25, 3.7, 2.6, 0.7),
    ("Romaine Lettuce", "g", 17, 3.3, 1.2, 0.3),
    ("Iceberg Lettuce", "g", 14, 3.0, 0.9, 0.1),
    ("Watercress", "g", 11, 1.3, 2.3, 0.1),
    ("Bok Choy", "g", 13, 2.2, 1.5, 0.2),
    ("Cucumber", "g", 15, 3.6, 0.7, 0.1),
    ("Zucchini", "g", 17, 3.1, 1.2, 0.3),
    ("Eggplant", "g", 25, 6.0, 1.0, 0.2),
    ("White Mushroom", "g", 22, 3.3, 3.1, 0.3),
    ("Cremini Mushroom", "g", 22, 4.3, 2.5, 0.1),
    ("Portobello Mushroom", "g", 22, 3.9, 2.1, 0.4),
    ("Shiitake Mushroom", "g", 34, 6.8, 2.2, 0.5),
    ("Pumpkin", "g", 26, 6.5, 1.0, 0.1),
    ("Butternut Squash", "g", 45, 12.0, 1.0, 0.1),
    ("Asparagus", "g", 20, 3.9, 2.2, 0.1),
    ("Green Beans", "g", 31, 7.0, 1.8, 0.2),
    ("Peas", "g", 81, 14.5, 5.4, 0.4),
    ("Snow Peas", "g", 42, 7.5, 2.8, 0.2),
    ("Corn", "g", 86, 19.0, 3.3, 1.4),
    ("Beetroot", "g", 43, 9.6, 1.6, 0.2),
    ("Radish", "g", 16, 3.4, 0.7, 0.1),
    ("Turnip", "g", 28, 6.4, 0.9, 0.1),
    ("Parsnip", "g", 75, 18.0, 1.2, 0.3),
    ("Fennel", "g", 31, 7.3, 1.2, 0.2),
    ("Artichoke", "g", 47, 10.5, 3.3, 0.2),
    ("Okra", "g", 33, 7.5, 1.9, 0.2),
    ("Bean Sprouts", "g", 31, 5.9, 3.0, 0.2),
    ("Avocado", "g", 160, 8.5, 2.0, 14.7),
]

FRUITS = [
    ("Apple", "g", 52, 13.8, 0.3, 0.2),
    ("Banana", "g", 89, 22.8, 1.1, 0.3),
    ("Orange", "g", 47, 11.8, 0.9, 0.1),
    ("Lemon", "g", 29, 9.3, 1.1, 0.3),
    ("Lime", "g", 30, 10.5, 0.7, 0.2),
    ("Grapefruit", "g", 42, 10.7, 0.8, 0.1),
    ("Strawberry", "g", 32, 7.7, 0.7, 0.3),
    ("Blueberry", "g", 57, 14.5, 0.7, 0.3),
    ("Raspberry", "g", 52, 11.9, 1.2, 0.7),
    ("Blackberry", "g", 43, 9.6, 1.4, 0.5),
    ("Cranberry", "g", 46, 12.2, 0.4, 0.1),
    ("Grape Red", "g", 69, 18.1, 0.7, 0.2),
    ("Watermelon", "g", 30, 7.6, 0.6, 0.2),
    ("Cantaloupe", "g", 34, 8.2, 0.8, 0.2),
    ("Honeydew Melon", "g", 36, 9.1, 0.5, 0.1),
    ("Pineapple", "g", 50, 13.1, 0.5, 0.1),
    ("Mango", "g", 60, 15.0, 0.8, 0.4),
    ("Papaya", "g", 43, 10.8, 0.5, 0.3),
    ("Kiwi", "g", 61, 14.7, 1.1, 0.5),
    ("Peach", "g", 39, 9.5, 0.9, 0.3),
    ("Nectarine", "g", 44, 10.6, 1.1, 0.3),
    ("Plum", "g", 46, 11.4, 0.7, 0.3),
    ("Apricot", "g", 48, 11.1, 1.4, 0.4),
    ("Cherry", "g", 63, 16.0, 1.1, 0.2),
    ("Pear", "g", 57, 15.2, 0.4, 0.1),
    ("Fig", "g", 74, 19.2, 0.8, 0.3),
    ("Date", "g", 277, 75.0, 1.8, 0.2),
    ("Pomegranate", "g", 83, 18.7, 1.7, 1.2),
    ("Passion Fruit", "g", 97, 23.4, 2.2, 0.7),
    ("Coconut Meat", "g", 354, 15.2, 3.3, 33.5),
    ("Raisins", "g", 299, 79.2, 3.1, 0.5),
    ("Dried Cranberries", "g", 308, 82.0, 0.1, 1.4),
    ("Dried Apricots", "g", 241, 63.0, 3.4, 0.5),
    ("Prunes", "g", 240, 63.9, 2.2, 0.4),
    ("Mandarin Orange", "g", 53, 13.3, 0.8, 0.3),
    ("Persimmon", "g", 70, 18.6, 0.6, 0.2),
    ("Guava", "g", 68, 14.3, 2.6, 1.0),
    ("Lychee", "g", 66, 16.5, 0.8, 0.4),
]

MEAT_AND_POULTRY = [
    ("Chicken Breast", "g", 165, 0, 31.0, 3.6),
    ("Chicken Thigh", "g", 209, 0, 26.0, 10.9),
    ("Chicken Wing", "g", 203, 0, 30.5, 8.1),
    ("Chicken Drumstick", "g", 172, 0, 28.3, 5.7),
    ("Ground Chicken", "g", 143, 0, 17.4, 8.1),
    ("Turkey Breast", "g", 135, 0, 30.0, 0.7),
    ("Ground Turkey", "g", 170, 0, 21.0, 9.4),
    ("Beef Sirloin", "g", 183, 0, 26.1, 8.2),
    ("Beef Tenderloin", "g", 218, 0, 26.0, 12.0),
    ("Ground Beef Lean", "g", 250, 0, 26.1, 15.0),
    ("Ground Beef Regular", "g", 332, 0, 14.4, 30.0),
    ("Beef Chuck", "g", 250, 0, 26.4, 15.4),
    ("Beef Ribeye", "g", 291, 0, 24.8, 20.7),
    ("Veal", "g", 172, 0, 24.0, 8.0),
    ("Pork Loin", "g", 143, 0, 27.3, 3.5),
    ("Pork Chop", "g", 231, 0, 25.7, 13.5),
    ("Pork Tenderloin", "g", 143, 0, 26.2, 3.5),
    ("Ground Pork", "g", 263, 0, 16.9, 21.2),
    ("Bacon", "g", 541, 1.4, 37.0, 41.8),
    ("Pancetta", "g", 450, 0, 15.0, 45.0),
    ("Prosciutto", "g", 195, 0.7, 24.1, 10.4),
    ("Ham", "g", 145, 1.5, 21.0, 5.5),
    ("Lamb Leg", "g", 162, 0, 25.5, 6.3),
    ("Lamb Chop", "g", 294, 0, 24.5, 20.9),
    ("Ground Lamb", "g", 282, 0, 16.6, 23.4),
    ("Duck Breast", "g", 201, 0, 23.5, 11.2),
    ("Italian Sausage", "g", 301, 1.3, 14.2, 26.3),
    ("Chorizo", "g", 455, 1.9, 24.1, 38.3),
]

FISH_AND_SEAFOOD = [
    ("Salmon", "g", 208, 0, 20.4, 13.4),
    ("Smoked Salmon", "g", 117, 0, 18.3, 4.3),
    ("Tuna Fresh", "g", 144, 0, 23.3, 4.9),
    ("Tuna Canned", "g", 116, 0, 25.5, 0.8),
    ("Cod", "g", 82, 0, 17.8, 0.7),
    ("Tilapia", "g", 96, 0, 20.1, 1.7),
    ("Shrimp", "g", 99, 0.2, 24.0, 0.3),
    ("Prawns", "g", 106, 0.9, 20.3, 1.7),
    ("Scallops", "g", 69, 3.2, 12.1, 0.5),
    ("Mussels", "g", 86, 3.7, 11.9, 2.2),
    ("Clams", "g", 86, 3.6, 14.7, 1.0),
    ("Squid", "g", 92, 3.1, 15.6, 1.4),
    ("Octopus", "g", 82, 2.2, 14.9, 1.0),
    ("Crab Meat", "g", 87, 0, 18.1, 1.1),
    ("Lobster", "g", 89, 0, 19.0, 0.9),
    ("Sardines", "g", 208, 0, 24.6, 11.5),
    ("Mackerel", "g", 205, 0, 18.6, 13.9),
    ("Sea Bass", "g", 97, 0, 18.4, 2.0),
    ("Swordfish", "g", 144, 0, 23.5, 5.0),
    ("Trout", "g", 148, 0, 20.8, 6.6),
    ("Anchovies", "g", 131, 0, 20.4, 4.8),
    ("Halibut", "g", 111, 0, 22.5, 1.6),
]

DAIRY_AND_EGGS = [
    ("Whole Milk", "ml", 61, 4.8, 3.2, 3.3),
    ("Skim Milk", "ml", 34, 5.0, 3.4, 0.1),
    ("Heavy Cream", "ml", 340, 2.8, 2.1, 36.1),
    ("Sour Cream", "g", 193, 4.6, 2.1, 19.4),
    ("Greek Yogurt", "g", 97, 3.6, 9.0, 5.0),
    ("Plain Yogurt", "g", 61, 4.7, 3.5, 3.3),
    ("Cottage Cheese", "g", 98, 3.4, 11.1, 4.3),
    ("Cream Cheese", "g", 342, 4.1, 5.9, 34.2),
    ("Cheddar Cheese", "g", 403, 1.3, 24.9, 33.1),
    ("Mozzarella Cheese", "g", 280, 3.1, 28.0, 17.0),
    ("Parmesan Cheese", "g", 431, 3.2, 38.5, 29.0),
    ("Feta Cheese", "g", 264, 4.1, 14.2, 21.3),
    ("Gouda Cheese", "g", 356, 2.2, 24.9, 27.4),
    ("Brie Cheese", "g", 334, 0.5, 20.8, 27.7),
    ("Ricotta Cheese", "g", 174, 3.0, 11.3, 13.0),
    ("Swiss Cheese", "g", 380, 5.4, 26.9, 27.8),
    ("Goat Cheese", "g", 364, 0.1, 21.6, 29.8),
    ("Blue Cheese", "g", 353, 2.3, 21.4, 28.7),
    ("Mascarpone", "g", 429, 4.8, 4.8, 44.6),
    ("Butter", "g", 717, 0.1, 0.9, 81.0),
    ("Ghee", "g", 900, 0, 0, 100.0),
    ("Egg", "pcs", 155, 1.1, 13.0, 11.0),
    ("Egg White", "ml", 52, 0.7, 10.9, 0.2),
    ("Egg Yolk", "g", 322, 3.6, 16.0, 26.5),
    ("Condensed Milk", "ml", 321, 54.4, 7.9, 8.7),
    ("Evaporated Milk", "ml", 134, 10.0, 6.8, 7.6),
    ("Whipping Cream", "ml", 292, 2.8, 2.5, 30.9),
    ("Buttermilk", "ml", 40, 4.8, 3.3, 0.9),
    ("Coconut Milk", "ml", 230, 6.0, 2.3, 23.8),
    ("Coconut Cream", "ml", 330, 6.7, 3.3, 34.7),
]

GRAINS_PASTA_BREAD = [
    ("White Rice", "g", 130, 28.2, 2.7, 0.3),
    ("Brown Rice", "g", 111, 23.0, 2.6, 0.9),
    ("Basmati Rice", "g", 121, 25.2, 3.5, 0.4),
    ("Jasmine Rice", "g", 129, 28.0, 2.7, 0.3),
    ("Wild Rice", "g", 101, 21.3, 4.0, 0.3),
    ("Arborio Rice", "g", 130, 28.0, 2.4, 0.3),
    ("Quinoa", "g", 120, 21.3, 4.4, 1.9),
    ("Couscous", "g", 112, 23.2, 3.8, 0.2),
    ("Bulgur", "g", 83, 18.6, 3.1, 0.2),
    ("Oats", "g", 389, 66.3, 16.9, 6.9),
    ("Spaghetti", "g", 131, 25.0, 5.0, 1.1),
    ("Penne", "g", 131, 25.0, 5.0, 1.1),
    ("Fusilli", "g", 131, 25.0, 5.0, 1.1),
    ("Fettuccine", "g", 131, 25.0, 5.0, 1.1),
    ("Lasagna Sheets", "g", 131, 25.0, 5.0, 1.1),
    ("Egg Noodles", "g", 138, 25.2, 4.5, 2.1),
    ("Rice Noodles", "g", 109, 24.9, 0.9, 0.2),
    ("Udon Noodles", "g", 99, 21.6, 2.6, 0.1),
    ("White Bread", "g", 265, 49.0, 9.0, 3.2),
    ("Whole Wheat Bread", "g", 247, 41.3, 13.0, 3.4),
    ("Sourdough Bread", "g", 274, 51.9, 10.9, 2.4),
    ("Flour Tortilla", "pcs", 312, 52.4, 8.4, 8.0),
    ("Corn Tortilla", "pcs", 218, 44.6, 5.7, 2.9),
    ("Pita Bread", "g", 275, 55.7, 9.1, 1.2),
    ("Breadcrumbs", "g", 395, 72.0, 13.3, 5.3),
    ("Panko Breadcrumbs", "g", 395, 72.0, 12.0, 4.0),
    ("Polenta", "g", 85, 18.4, 2.0, 0.5),
    ("Granola", "g", 489, 64.0, 10.0, 24.0),
]

LEGUMES = [
    ("Black Beans", "g", 132, 23.7, 8.9, 0.5),
    ("Kidney Beans", "g", 127, 22.8, 8.7, 0.5),
    ("Chickpeas", "g", 164, 27.4, 8.9, 2.6),
    ("Green Lentils", "g", 116, 20.1, 9.0, 0.4),
    ("Red Lentils", "g", 116, 20.1, 9.0, 0.4),
    ("White Beans", "g", 139, 25.1, 9.7, 0.4),
    ("Lima Beans", "g", 115, 20.9, 7.8, 0.4),
    ("Edamame", "g", 121, 8.9, 11.9, 5.2),
    ("Tofu Firm", "g", 76, 1.9, 8.1, 4.8),
    ("Tofu Silken", "g", 55, 2.4, 4.8, 2.7),
    ("Tempeh", "g", 192, 7.6, 20.3, 10.8),
    ("Pinto Beans", "g", 143, 26.2, 9.0, 0.7),
    ("Navy Beans", "g", 140, 26.1, 8.2, 0.6),
    ("Mung Beans", "g", 105, 19.2, 7.0, 0.4),
]

NUTS_AND_SEEDS = [
    ("Almonds", "g", 579, 21.6, 21.2, 49.9),
    ("Walnuts", "g", 654, 13.7, 15.2, 65.2),
    ("Cashews", "g", 553, 30.2, 18.2, 43.9),
    ("Pecans", "g", 691, 13.9, 9.2, 72.0),
    ("Pistachios", "g", 560, 27.2, 20.2, 45.3),
    ("Peanuts", "g", 567, 16.1, 25.8, 49.2),
    ("Hazelnuts", "g", 628, 16.7, 15.0, 60.8),
    ("Macadamia Nuts", "g", 718, 13.8, 7.9, 75.8),
    ("Pine Nuts", "g", 673, 13.1, 13.7, 68.4),
    ("Brazil Nuts", "g", 656, 12.3, 14.3, 66.4),
    ("Sunflower Seeds", "g", 584, 20.0, 20.8, 51.5),
    ("Pumpkin Seeds", "g", 559, 10.7, 30.2, 49.1),
    ("Chia Seeds", "g", 486, 42.1, 16.5, 30.7),
    ("Flax Seeds", "g", 534, 28.9, 18.3, 42.2),
    ("Sesame Seeds", "g", 573, 23.5, 17.7, 49.7),
    ("Hemp Seeds", "g", 553, 8.7, 31.6, 48.8),
    ("Poppy Seeds", "g", 525, 28.1, 17.9, 41.6),
    ("Peanut Butter", "g", 588, 20.0, 25.0, 50.4),
    ("Almond Butter", "g", 614, 18.8, 21.0, 55.5),
    ("Tahini", "g", 595, 21.2, 17.0, 53.8),
]

FRESH_HERBS = [
    ("Basil Fresh", "g", 23, 2.7, 3.2, 0.6),
    ("Parsley Fresh", "g", 36, 6.3, 3.0, 0.8),
    ("Cilantro Fresh", "g", 23, 3.7, 2.1, 0.5),
    ("Mint Fresh", "g", 44, 8.4, 3.3, 0.7),
    ("Dill Fresh", "g", 43, 7.0, 3.5, 1.1),
    ("Rosemary Fresh", "g", 131, 20.7, 3.3, 5.9),
    ("Thyme Fresh", "g", 101, 24.5, 5.6, 1.7),
    ("Sage Fresh", "g", 63, 11.2, 3.5, 1.3),
    ("Oregano Fresh", "g", 44, 8.3, 1.5, 1.0),
    ("Chives Fresh", "g", 30, 4.4, 3.3, 0.7),
    ("Tarragon Fresh", "g", 50, 7.0, 3.5, 1.1),
    ("Lemongrass", "g", 99, 25.3, 1.8, 0.5),
    ("Thai Basil", "g", 23, 2.7, 3.2, 0.6),
    ("Bay Leaves", "g", 313, 75.0, 7.6, 8.4),
]

DRIED_SPICES = [
    ("Salt", "g", 0, 0, 0, 0),
    ("Black Pepper", "g", 251, 63.9, 10.4, 3.3),
    ("White Pepper", "g", 296, 68.6, 10.4, 2.1),
    ("Paprika", "g", 282, 53.9, 14.1, 12.9),
    ("Smoked Paprika", "g", 282, 54.0, 14.1, 12.9),
    ("Cayenne Pepper", "g", 318, 56.6, 12.0, 17.3),
    ("Cumin", "g", 375, 44.2, 17.8, 22.3),
    ("Coriander Ground", "g", 298, 54.9, 12.4, 17.8),
    ("Turmeric", "g", 354, 64.9, 7.8, 9.9),
    ("Cinnamon", "g", 247, 80.6, 4.0, 1.2),
    ("Nutmeg", "g", 525, 49.3, 5.8, 36.3),
    ("Cloves", "g", 274, 65.5, 6.0, 13.0),
    ("Cardamom", "g", 311, 68.5, 10.8, 6.7),
    ("Ginger Ground", "g", 335, 71.6, 9.0, 4.2),
    ("Chili Flakes", "g", 314, 56.6, 12.0, 17.3),
    ("Oregano Dried", "g", 265, 68.9, 9.0, 4.3),
    ("Basil Dried", "g", 233, 47.8, 14.4, 4.1),
    ("Thyme Dried", "g", 276, 63.9, 9.1, 7.4),
    ("Rosemary Dried", "g", 331, 64.1, 4.9, 15.2),
    ("Saffron", "g", 310, 65.4, 11.4, 5.9),
    ("Mustard Seeds", "g", 508, 28.1, 26.1, 36.2),
    ("Fennel Seeds", "g", 345, 52.3, 15.8, 14.9),
    ("Star Anise", "g", 337, 50.0, 18.0, 16.0),
    ("Allspice", "g", 263, 72.1, 6.1, 8.7),
    ("Garlic Powder", "g", 331, 72.7, 16.6, 0.7),
    ("Onion Powder", "g", 341, 79.1, 10.4, 1.0),
    ("Curry Powder", "g", 325, 55.8, 14.3, 14.0),
    ("Garam Masala", "g", 379, 45.0, 15.0, 15.0),
]

OILS_AND_FATS = [
    ("Olive Oil", "ml", 884, 0, 0, 100.0),
    ("Extra Virgin Olive Oil", "ml", 884, 0, 0, 100.0),
    ("Coconut Oil", "ml", 862, 0, 0, 100.0),
    ("Vegetable Oil", "ml", 884, 0, 0, 100.0),
    ("Canola Oil", "ml", 884, 0, 0, 100.0),
    ("Sesame Oil", "ml", 884, 0, 0, 100.0),
    ("Sunflower Oil", "ml", 884, 0, 0, 100.0),
    ("Avocado Oil", "ml", 884, 0, 0, 100.0),
    ("Walnut Oil", "ml", 884, 0, 0, 100.0),
    ("Truffle Oil", "ml", 884, 0, 0, 100.0),
    ("Cooking Spray", "ml", 0, 0, 0, 0),
    ("Lard", "g", 902, 0, 0, 100.0),
]

CONDIMENTS_AND_SAUCES = [
    ("Soy Sauce", "ml", 53, 4.9, 8.1, 0.6),
    ("Fish Sauce", "ml", 35, 3.6, 5.1, 0.0),
    ("Worcestershire Sauce", "ml", 78, 19.5, 0, 0),
    ("Hot Sauce", "ml", 11, 1.8, 0.5, 0.4),
    ("Sriracha", "ml", 93, 18.5, 1.9, 1.0),
    ("Tomato Paste", "g", 82, 18.9, 4.3, 0.5),
    ("Tomato Sauce", "g", 29, 5.4, 1.3, 0.2),
    ("Ketchup", "g", 112, 27.4, 1.7, 0.1),
    ("Yellow Mustard", "g", 66, 5.3, 4.4, 3.3),
    ("Dijon Mustard", "g", 66, 5.3, 4.4, 3.3),
    ("Mayonnaise", "g", 680, 0.6, 1.0, 75.0),
    ("Apple Cider Vinegar", "ml", 21, 0.9, 0, 0),
    ("Balsamic Vinegar", "ml", 88, 17.0, 0.5, 0),
    ("Red Wine Vinegar", "ml", 19, 0.3, 0, 0),
    ("White Wine Vinegar", "ml", 18, 0.3, 0, 0),
    ("Rice Vinegar", "ml", 18, 0, 0, 0),
    ("Hoisin Sauce", "ml", 220, 44.0, 3.5, 3.4),
    ("Oyster Sauce", "ml", 51, 11.0, 1.4, 0),
    ("Miso Paste", "g", 199, 26.5, 11.7, 6.0),
    ("Honey", "g", 304, 82.4, 0.3, 0),
    ("Maple Syrup", "ml", 260, 67.0, 0, 0.1),
    ("Coconut Aminos", "ml", 25, 6.0, 0, 0),
    ("Pesto Sauce", "g", 316, 6.0, 5.0, 30.0),
]

BAKING = [
    ("All-Purpose Flour", "g", 364, 76.3, 10.3, 1.0),
    ("Whole Wheat Flour", "g", 340, 72.6, 13.2, 2.5),
    ("Almond Flour", "g", 571, 21.4, 21.0, 50.6),
    ("Coconut Flour", "g", 400, 60.0, 20.0, 10.0),
    ("Cornstarch", "g", 381, 91.3, 0.3, 0.1),
    ("Baking Powder", "g", 53, 27.7, 0, 0),
    ("Baking Soda", "g", 0, 0, 0, 0),
    ("Active Dry Yeast", "g", 325, 41.2, 40.4, 7.6),
    ("White Sugar", "g", 387, 100, 0, 0),
    ("Brown Sugar", "g", 380, 98.1, 0, 0),
    ("Powdered Sugar", "g", 389, 100, 0, 0),
    ("Vanilla Extract", "ml", 288, 12.7, 0.1, 0.1),
    ("Cocoa Powder", "g", 228, 57.9, 19.6, 13.7),
    ("Dark Chocolate", "g", 546, 59.4, 5.5, 31.3),
    ("Milk Chocolate", "g", 535, 59.4, 7.6, 29.7),
    ("White Chocolate", "g", 539, 59.2, 5.9, 32.1),
    ("Gelatin", "g", 335, 0, 85.6, 0.1),
    ("Corn Syrup", "ml", 286, 77.5, 0, 0),
]

BEVERAGES_AND_MISC = [
    ("Chicken Broth", "ml", 7, 0.3, 1.1, 0.2),
    ("Beef Broth", "ml", 7, 0.1, 1.1, 0.3),
    ("Vegetable Broth", "ml", 6, 1.1, 0.2, 0),
    ("Coconut Water", "ml", 19, 3.7, 0.7, 0.2),
    ("Red Wine", "ml", 85, 2.6, 0.1, 0),
    ("White Wine", "ml", 82, 2.6, 0.1, 0),
    ("Orange Juice", "ml", 45, 10.4, 0.7, 0.2),
    ("Lemon Juice", "ml", 22, 6.9, 0.4, 0.2),
    ("Lime Juice", "ml", 25, 8.4, 0.4, 0.1),
    ("Capers", "g", 23, 4.9, 2.4, 0.9),
    ("Black Olives", "g", 115, 6.3, 0.8, 10.7),
    ("Green Olives", "g", 145, 3.8, 1.0, 15.3),
    ("Pickles", "g", 11, 2.3, 0.3, 0.2),
    ("Nori Seaweed", "g", 35, 5.1, 5.8, 0.3),
    ("Tortilla Chips", "g", 489, 63.0, 7.0, 24.0),
    ("Toasted Sesame Oil", "ml", 884, 0, 0, 100.0),
    ("Paneer", "g", 265, 1.2, 18.3, 20.8),
    ("Kimchi", "g", 15, 2.4, 1.1, 0.5),
]

# ---------------------------------------------------------------------------
# Combine all categories
# ---------------------------------------------------------------------------
ALL_INGREDIENTS = (
    VEGETABLES
    + FRUITS
    + MEAT_AND_POULTRY
    + FISH_AND_SEAFOOD
    + DAIRY_AND_EGGS
    + GRAINS_PASTA_BREAD
    + LEGUMES
    + NUTS_AND_SEEDS
    + FRESH_HERBS
    + DRIED_SPICES
    + OILS_AND_FATS
    + CONDIMENTS_AND_SAUCES
    + BAKING
    + BEVERAGES_AND_MISC
)


# ---------------------------------------------------------------------------
# Init helpers
# ---------------------------------------------------------------------------
def build_ingredient(name, units, cal, carbs, prot, fat):
    """Build an Ingredient Pydantic model with a deterministic _id."""
    return Ingredient(
        id=make_ingredient_id(name),
        name=name,
        units=units,
        image=None,
        macro_per_hundred=Macro(calories=cal, carbs=carbs, proteins=prot, fats=fat),
    )


async def init_ingredients():
    """Seed the ingredients collection (idempotent — skips if data exists)."""
    try:
        print("Connecting to MongoDB…")
        await connect_to_mongodb()

        db = get_database()
        collection = db[settings.INGREDIENTS_COLLECTION]

        existing_count = await collection.count_documents({})
        if existing_count > 0:
            print(f"⚠️  Collection already has {existing_count} ingredients — skipping.")
            return

        docs = []
        for row in ALL_INGREDIENTS:
            ingredient = build_ingredient(*row)
            docs.append(ingredient.model_dump(by_alias=True))

        result = await collection.insert_many(docs)

        print(f"✅ Inserted {len(result.inserted_ids)} ingredients.")
        print(f"   Categories: Vegetables({len(VEGETABLES)}), Fruits({len(FRUITS)}), "
              f"Meat({len(MEAT_AND_POULTRY)}), Seafood({len(FISH_AND_SEAFOOD)}), "
              f"Dairy({len(DAIRY_AND_EGGS)}), Grains({len(GRAINS_PASTA_BREAD)}), "
              f"Legumes({len(LEGUMES)}), Nuts({len(NUTS_AND_SEEDS)}), "
              f"Herbs({len(FRESH_HERBS)}), Spices({len(DRIED_SPICES)}), "
              f"Oils({len(OILS_AND_FATS)}), Condiments({len(CONDIMENTS_AND_SAUCES)}), "
              f"Baking({len(BAKING)}), Misc({len(BEVERAGES_AND_MISC)})")
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        await disconnect_from_mongodb()


if __name__ == "__main__":
    print(f"Total ingredients to seed: {len(ALL_INGREDIENTS)}")
    asyncio.run(init_ingredients())
