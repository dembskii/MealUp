from pydantic_settings import BaseSettings
from typing import List, Optional
from pathlib import Path

class Settings(BaseSettings):
    # Project
    PROJECT_NAME: str = "Forum Service"
    VERSION: str = "1.0.0"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8001",
        "http://localhost:8002"
    ]

    #Postgres
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_FORUM_DB: str
    FORUM_DATABASE_URL: str

    RECIPE_SERVICE_URL: str
    WORKOUT_SERVICE_URL: str
    
    #Redis
    AUTH_REDIS_PASSWORD: str
    REDIS_AUTH_URL: str

    AUTH0_DOMAIN: str
    AUTH0_AUDIENCE: Optional[str] = None
    ALGORITHMS: str
    
    class Config:
        env_file = ".env.local" if Path(".env.local").exists() else ".env"
        case_sensitive = True

settings = Settings()