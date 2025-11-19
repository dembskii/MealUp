from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.api.routes import router
from src.core.config import settings
from src.middleware.logging import RequestLoggingMiddleware
from src.services.redis_service import redis_service
import logging

logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown"""
    logger.info("Starting up Auth Service...")
    await redis_service.connect()
    logger.info("Redis service initialized")
    
    yield
    
    logger.info("Shutting down Auth Service...")
    await redis_service.disconnect()
    logger.info("Redis service closed")


app = FastAPI(
    title = "Auth Service",
    version = "1.0.0",
    description = "Authentication Service with Auth0",
    lifespan = lifespan
)


# Add logging middleware
app.add_middleware(RequestLoggingMiddleware)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins = settings.ALLOWED_ORIGINS,
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)


# Include routers
app.include_router(router, prefix = "/auth")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "auth-service"}


if __name__ == "__main__":
    uvicorn.run(app, host = "0.0.0.0", port=  8001)