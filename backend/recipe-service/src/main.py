from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.core.config import settings
import logging

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
    description = "Receipe Service for MealUp",
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


# Include routers
#app.include_router(router, prefix="/recipe")


@app.get("/")
async def root():
    return {"message": "Recipe Service is running", "version": settings.VERSION}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host = "0.0.0.0", port = 8003)