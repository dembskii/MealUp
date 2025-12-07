from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path


class Settings(BaseSettings):
    # Project
    PROJECT_NAME: str = "Workout Service"
    VERSION: str = "1.0.0"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8001"
    ]

    # MongoDB
    WORKOUT_MONGODB_URL: str
    MONGODB_DB_NAME: str = "workout_db"
    
    # MongoDB Collections
    EXERCISES_COLLECTION: str = "exercises"
    TRAININGS_COLLECTION: str = "trainings"
    WORKOUT_PLANS_COLLECTION: str = "workout_plans"
    
    # Alias for consistency with mongodb.py
    @property
    def MONGODB_URL(self) -> str:
        return self.WORKOUT_MONGODB_URL
    
    class Config:
        env_file = ".env.local" if Path(".env.local").exists() else ".env"
        case_sensitive = True


settings = Settings()
