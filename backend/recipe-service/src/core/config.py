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
    RECIPE_MONGODB_URL: str
    MONGODB_DB_NAME: str = "recipe_db"
    
    # MongoDB Collections
    RECIPES_COLLECTION: str = "recipes"
    INGREDIENTS_COLLECTION: str = "ingredients"
    RECIPE_VERSIONS_COLLECTION: str = "recipe_versions"

    AUTH0_DOMAIN: str
    AUTH0_AUDIENCE: Optional[str] = None
    ALGORITHMS: str
    OPEN_ROUTER_API_KEY: str
    
    # Alias for consistency with mongodb.py
    @property
    def MONGODB_URL(self) -> str:
        return self.RECIPE_MONGODB_URL
    
    
    class Config:
        env_file = ".env.local" if Path(".env.local").exists() else ".env"
        case_sensitive = True

settings = Settings()