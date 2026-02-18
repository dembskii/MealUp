from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.core.config import settings
from src.db.mongodb import connect_to_mongodb, disconnect_from_mongodb
from src.api.routes import router as analytics_router
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Server is starting...")
    # Connect to MongoDB
    await connect_to_mongodb()
    yield
    # Disconnect from MongoDB
    await disconnect_from_mongodb()
    logger.info("Server has been stopped")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Analytics Service for MealUp – calorie & macronutrient tracking",
    lifespan=lifespan
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])


@app.get("/")
async def root():
    return {"message": "Analytics Service is running", "version": settings.VERSION}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "analytics-service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
