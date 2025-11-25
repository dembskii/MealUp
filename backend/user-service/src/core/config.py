from pydantic_settings import BaseSettings
from typing import List, Optional
from pathlib import Path
import os

class Settings(BaseSettings):
    # Project
    PROJECT_NAME: str = "User Service"
    VERSION: str = "1.0.0"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8001"
    ]

    #Postgres
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_USER_DB: str
    USER_DATABASE_URL: str
    
    #Redis
    AUTH_REDIS_PASSWORD: str
    REDIS_AUTH_URL: str
    
    class Config:
        env_file = ".env.local" if Path(".env.local").exists() else ".env"
        case_sensitive = True

settings = Settings()