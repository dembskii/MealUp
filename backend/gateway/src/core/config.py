from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "API Gateway"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Service URLs
    AUTH_SERVICE_URL: str = "http://localhost:8001"
    USER_SERVICE_URL: str = "http://localhost:8002"
    
    # Timeout settings (in seconds)
    REQUEST_TIMEOUT: float = 30.0
    CONNECT_TIMEOUT: float = 5.0
    
    # Retry settings
    MAX_RETRIES: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()