from pydantic_settings import BaseSettings
from typing import List, Optional
from pathlib import Path
import os

class Settings(BaseSettings):
    # Project
    PROJECT_NAME: str = "Recipe Service"
    VERSION: str = "1.0.0"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8001"
    ]

    # MongoDB
    MONGODB_URL: str
    MONGODB_DB_NAME: str = "recipe_service"
    
    # MongoDB Collections
    RECIPES_COLLECTION: str = "recipes"
    INGREDIENTS_COLLECTION: str = "ingredients"
    
    # Redis
    AUTH_REDIS_PASSWORD: str
    REDIS_AUTH_URL: str
    
    class Config:
        env_file = ".env.local" if Path(".env.local").exists() else ".env"
        case_sensitive = True

settings = Settings()