from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.core.config import settings
from sqlmodel import SQLModel
import logging

from src.api import posts as post_routes
from src.api import comments as comment_routes
from src.api import search as search_routes

logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Server is starting...")
    yield
    print(f"Server has been stopped")


app = FastAPI(
    title = settings.PROJECT_NAME,
    version = settings.VERSION,
    description = "Forum Service for MealUp",
    lifespan = lifespan
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins = settings.ALLOWED_ORIGINS,
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)


# Include API routers
app.include_router(post_routes.router, prefix="/forum", tags=["posts"])
app.include_router(comment_routes.router, prefix="/forum", tags=["comments"])
app.include_router(search_routes.router, prefix="/forum", tags=["search"]) 


@app.get("/")
async def root():
    return {"message": "Forum Service is running", "version": settings.VERSION}


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker"""
    return {"status": "healthy", "service": "user-service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host = "0.0.0.0", port = 8007)