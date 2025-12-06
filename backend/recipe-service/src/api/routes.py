import uuid
import logging
from typing import Optional
from urllib.parse import urlencode
from fastapi import APIRouter, HTTPException, Response, Cookie, Request, Query, Header

from src.core.config import settings
from src.models.model import (
    Recipe,
    RecipeCreate,
    RecipeUpdate,
    RecipeResponse
)
from src.services.recipe_service import RecipeService


logger = logging.getLogger(__name__)
router = APIRouter()


def get_user_id_from_header(x_user_id: Optional[str] = Header(None)) -> str:
    """Extract user ID from header (set by gateway after auth)"""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    return x_user_id


@router.get("/", response_model=list[RecipeResponse])
async def get_recipes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    author_id: Optional[str] = Query(None)
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
    x_user_id: str = Header(None, alias="X-User-Id")
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
async def get_recipe(recipe_id: str):
    """Get a recipe by ID"""
    recipe = await RecipeService.get_recipe(recipe_id)
    
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    return recipe


@router.put("/{recipe_id}", response_model=RecipeResponse)
async def update_recipe(
    recipe_id: str,
    recipe_update: RecipeUpdate,
    x_user_id: str = Header(None, alias="X-User-Id")
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
    x_user_id: str = Header(None, alias="X-User-Id")
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
async def like_recipe(recipe_id: str):
    """Like a recipe (increment like count)"""
    recipe = await RecipeService.like_recipe(recipe_id)
    
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    return recipe


@router.post("/{recipe_id}/unlike", response_model=RecipeResponse)
async def unlike_recipe(recipe_id: str):
    """Unlike a recipe (decrement like count)"""
    recipe = await RecipeService.unlike_recipe(recipe_id)
    
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    return recipe




