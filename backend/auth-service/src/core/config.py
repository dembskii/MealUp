from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # Project
    PROJECT_NAME: str = "Auth Service"
    VERSION: str = "1.0.0"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000"
    ]
    
    # Auth0
    AUTH0_DOMAIN: str
    AUTH0_CLIENT_ID: str
    AUTH0_CLIENT_SECRET: str
    AUTH0_REDIRECT_URI: str
    AUTH0_AUDIENCE: Optional[str] = None
    
    # Redis
    AUTH_REDIS_PASSWORD: str
    REDIS_AUTH_URL: str
    SESSION_EXPIRY: int = 86400
    
    # Frontend
    FRONTEND_URL: str

    #User-service
    USER_SERVICE_URL: str
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()