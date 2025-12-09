import uuid
import logging
from typing import Optional
from urllib.parse import urlencode
from fastapi import APIRouter, HTTPException, Query, Header, Depends

from src.core.config import settings
from src.models.model import (
    Recipe, RecipeCreate, RecipeUpdate, RecipeResponse,
    Ingredient, IngredientCreate, IngredientUpdate, IngredientResponse
)
from src.services.recipe_service import RecipeService, IngredientService
from typing import Dict

from common.auth_guard import require_auth 

logger = logging.getLogger(__name__)
router = APIRouter()


def get_user_id_from_header(x_user_id: Optional[str] = Header(None)) -> str:
    """Extract user ID from header (set by gateway after auth)"""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    return x_user_id


# ============ INGREDIENT ENDPOINTS ============

@router.get("/ingredients", response_model=list[IngredientResponse])
async def get_ingredients(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: Optional[str] = Query(None),
    token_payload: Dict = Depends(require_auth)
):
    """Get list of ingredients with optional search"""
    try:
        ingredients = await IngredientService.get_ingredients(skip, limit, search)
        return ingredients
    except Exception as e:
        logger.error(f"Error getting ingredients: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get ingredients")


@router.get("/ingredients/{ingredient_id}", response_model=IngredientResponse)
async def get_ingredient(
    ingredient_id: str,
    token_payload: Dict = Depends(require_auth)
):
    """Get an ingredient by ID"""
    ingredient = await IngredientService.get_ingredient(ingredient_id)
    
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    
    return ingredient


@router.post("/ingredients", response_model=IngredientResponse, status_code=201)
async def create_ingredient(
    ingredient_data: IngredientCreate, 
    token_payload: Dict = Depends(require_auth)
):
    """Create a new ingredient"""
    try:
        ingredient = await IngredientService.create_ingredient(ingredient_data)
        return ingredient
    except Exception as e:
        logger.error(f"Error creating ingredient: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create ingredient")


@router.put("/ingredients/{ingredient_id}", response_model=IngredientResponse)
async def update_ingredient(
    ingredient_id: str,
    ingredient_update: IngredientUpdate,
    token_payload: Dict = Depends(require_auth)
):
    """Update an ingredient"""
    ingredient = await IngredientService.update_ingredient(ingredient_id, ingredient_update)
    
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    
    return ingredient


@router.delete("/ingredients/{ingredient_id}", status_code=204)
async def delete_ingredient(
    ingredient_id: str,
    token_payload: Dict = Depends(require_auth)
):
    """Delete an ingredient"""
    deleted = await IngredientService.delete_ingredient(ingredient_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    
    return None


# ============ RECIPE ENDPOINTS ============

@router.get("/", response_model=list[RecipeResponse])
async def get_recipes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    author_id: Optional[str] = Query(None),
    token_payload: Dict = Depends(require_auth)
):
    """Get list of recipes with pagination"""
    try:
        recipes = await RecipeService.get_recipes(skip, limit, author_id)
        return recipes
    except Exception as e:
        logger.error(f"Error getting recipes: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get recipes")


@router.post("/", response_model=RecipeResponse, status_code=201)
async def create_recipe(
    recipe_data: RecipeCreate,
    x_user_id: str = Header(None, alias="X-User-Id"),
    token_payload: Dict = Depends(require_auth)
):
    """Create a new recipe"""
    user_id = get_user_id_from_header(x_user_id)
    
    try:
        recipe = await RecipeService.create_recipe(recipe_data, user_id)
        return recipe
    except Exception as e:
        logger.error(f"Error creating recipe: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create recipe")


@router.get("/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(
    recipe_id: str,
    token_payload: Dict = Depends(require_auth)
):
    """Get a recipe by ID"""
    recipe = await RecipeService.get_recipe(recipe_id)
    
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    return recipe


@router.put("/{recipe_id}", response_model=RecipeResponse)
async def update_recipe(
    recipe_id: str,
    recipe_update: RecipeUpdate,
    x_user_id: str = Header(None, alias="X-User-Id"),
    token_payload: Dict = Depends(require_auth)
):
    """Update a recipe (only by author)"""
    user_id = get_user_id_from_header(x_user_id)
    
    recipe = await RecipeService.update_recipe(recipe_id, recipe_update, user_id)
    
    if not recipe:
        raise HTTPException(
            status_code=404,
            detail="Recipe not found or you don't have permission to update it"
        )
    
    return recipe


@router.delete("/{recipe_id}", status_code=204)
async def delete_recipe(
    recipe_id: str,
    x_user_id: str = Header(None, alias="X-User-Id"),
    token_payload: Dict = Depends(require_auth)
):
    """Delete a recipe (only by author)"""
    user_id = get_user_id_from_header(x_user_id)
    
    deleted = await RecipeService.delete_recipe(recipe_id, user_id)
    
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Recipe not found or you don't have permission to delete it"
        )
    
    return None


@router.post("/{recipe_id}/like", response_model=RecipeResponse)
async def like_recipe(
    recipe_id: str,
    token_payload: Dict = Depends(require_auth)
):
    """Like a recipe (increment like count)"""
    recipe = await RecipeService.like_recipe(recipe_id)
    
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    return recipe


@router.post("/{recipe_id}/unlike", response_model=RecipeResponse)
async def unlike_recipe(
    recipe_id: str,
    token_payload: Dict = Depends(require_auth)
):
    """Unlike a recipe (decrement like count)"""
    recipe = await RecipeService.unlike_recipe(recipe_id)
    
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    return recipe




