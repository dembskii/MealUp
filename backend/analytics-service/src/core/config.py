from pydantic_settings import BaseSettings
from typing import List, Optional
from pathlib import Path


class Settings(BaseSettings):
    # Project
    PROJECT_NAME: str = "Analytics Service"
    VERSION: str = "1.0.0"

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8001"
    ]

    # MongoDB
    ANALYTICS_MONGODB_URL: str
    MONGODB_DB_NAME: str = "analytics_db"

    # MongoDB Collections
    DAILY_LOG_COLLECTION: str = "daily_logs"
    MEAL_ENTRIES_COLLECTION: str = "meal_entries"

    # Inter-service communication
    RECIPE_SERVICE_URL: str

    # Auth0
    AUTH0_DOMAIN: str
    AUTH0_AUDIENCE: Optional[str] = None
    ALGORITHMS: str

    @property
    def MONGODB_URL(self) -> str:
        return self.ANALYTICS_MONGODB_URL

    class Config:
        env_file = ".env.local" if Path(".env.local").exists() else ".env"
        case_sensitive = True


settings = Settings()
