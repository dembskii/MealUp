from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from enum import Enum
from datetime import datetime
import uuid


class CapacityUnit(str, Enum):
    """Enum for ingredient capacity/weight units"""
    GRAM = "g"
    KILOGRAM = "kg"
    MILLILITER = "ml"
    LITER = "l"
    TEASPOON = "tsp"
    TABLESPOON = "tbsp"
    CUP = "cup"
    OUNCE = "oz"
    POUND = "lb"
    PIECE = "pcs"


class Macro(BaseModel):
    """Macronutrient information per 100g"""
    calories: float = Field(..., ge=0, description="Calories per 100g")
    carbs: float = Field(..., ge=0, description="Carbohydrates per 100g in grams")
    proteins: float = Field(..., ge=0, description="Proteins per 100g in grams")
    fats: float = Field(..., ge=0, description="Fats per 100g in grams")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "calories": 50.0,
                "carbs": 10.0,
                "proteins": 2.0,
                "fats": 0.5,
            }
        }
    )


class Ingredient(BaseModel):
    """Ingredient document stored in MongoDB"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id", description="Unique ingredient ID")
    name: str = Field(..., min_length=1, max_length=100, description="Ingredient name")
    units: str = Field(..., min_length=1, max_length=20, description="Base unit of measurement")
    image: Optional[str] = Field(None, description="URL to ingredient image")
    macro_per_hundred: Optional[Macro] = Field(None, description="Macro nutrients per 100g")
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="_created_at")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="_updated_at")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Tomato",
                "units": "g",
                "image": "https://example.com/tomato.jpg",
                "macro_per_hundred": {
                    "calories": 18,
                    "carbs": 3.9,
                    "proteins": 0.9,
                    "fats": 0.2,
                },
            }
        }
    )


class WeightedIngredient(BaseModel):
    """Ingredient with specific quantity and unit for a recipe"""
    ingredient_id: str = Field(..., description="ID reference to the ingredient")
    capacity: CapacityUnit = Field(..., description="Unit of measurement for this recipe")
    quantity: float = Field(..., gt=0, description="Amount of ingredient needed")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ingredient_id": "550e8400-e29b-41d4-a716-446655440000",
                "capacity": "g",
                "quantity": 200.0,
            }
        }
    )


class Recipe(BaseModel):
    """Recipe document stored in MongoDB"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id", description="Unique recipe ID")
    name: str = Field(..., min_length=1, max_length=200, description="Recipe name")
    author_id: str = Field(..., description="User ID (auth0_sub) of recipe creator")
    ingredients: List[WeightedIngredient] = Field(..., min_length=1, description="List of weighted ingredients")
    prepare_instruction: List[str] = Field(..., min_length=1, description="Step-by-step preparation instructions")
    time_to_prepare: int = Field(..., gt=0, description="Time to prepare in seconds")
    image: Optional[str] = Field(None, description="Recipe Image in base64 format")
    total_likes: int = Field(default=0, ge=0, description="Total number of likes")
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="_created_at")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="_updated_at")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "_id": "650e8400-e29b-41d4-a716-446655440001",
                "name": "Tomato Pasta",
                "author_id": "google-oauth2|1234567890",
                "ingredients": [
                    {
                        "ingredient_id": "550e8400-e29b-41d4-a716-446655440000",
                        "capacity": "g",
                        "quantity": 400.0,
                    }
                ],
                "prepare_instruction": [
                    "Wash tomatoes",
                    "Cut into pieces",
                    "Cook for 20 minutes"
                ],
                "time_to_prepare": 1200,
                "images": ["https://example.com/recipe1.jpg", "https://example.com/recipe2.jpg"],
                "total_likes": 42,
            }
        }
    )


class RecipeCreate(BaseModel):
    """Schema for creating a new recipe"""
    name: str = Field(..., min_length=1, max_length=200)
    ingredients: List[WeightedIngredient] = Field(..., min_length=1)
    prepare_instruction: List[str] = Field(..., min_length=1, description="List of instruction steps")
    time_to_prepare: int = Field(..., gt=0, description="Time in seconds")
    image: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Tomato Pasta",
                "ingredients": [
                    {
                        "ingredient_id": "550e8400-e29b-41d4-a716-446655440000",
                        "capacity": "g",
                        "quantity": 400.0,
                    }
                ],
                "prepare_instruction": [
                    "Wash tomatoes",
                    "Cut into pieces",
                    "Cook for 20 minutes"
                ],
                "time_to_prepare": 1200,
                "images": ["https://example.com/recipe.jpg"],
            }
        }
    )


class RecipeUpdate(BaseModel):
    """Schema for updating an existing recipe"""
    ingredients: Optional[List[WeightedIngredient]] = None
    prepare_instruction: Optional[str] = Field(None, min_length=1)
    time_to_prepare: Optional[int] = Field(None, gt=0)
    image: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "prepare_instruction": "1. Wash\n2. Cut\n3. Cook for 25 minutes",
                "time_to_prepare": 1500,
            }
        }
    )


class IngredientCreate(BaseModel):
    """Schema for creating a new ingredient"""
    name: str = Field(..., min_length=1, max_length=100)
    units: str = Field(..., min_length=1, max_length=20)
    image: Optional[str] = None
    macro_per_hundred: Optional[Macro] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Tomato",
                "units": "g",
                "image": "https://example.com/tomato.jpg",
                "macro_per_hundred": {
                    "calories": 18,
                    "carbs": 3.9,
                    "proteins": 0.9,
                    "fats": 0.2,
                },
            }
        }
    )


class IngredientUpdate(BaseModel):
    """Schema for updating an ingredient"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    units: Optional[str] = Field(None, min_length=1, max_length=20)
    image: Optional[str] = None
    macro_per_hundred: Optional[Macro] = None


class RecipeResponse(Recipe):
    """Response schema for recipe endpoints"""
    pass


class IngredientResponse(Ingredient):
    """Response schema for ingredient endpoints"""
    pass
