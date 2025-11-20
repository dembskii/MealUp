from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import router
from src.core.config import settings
from src.middleware.logging import RequestLoggingMiddleware
from contextlib import asynccontextmanager
from src.services.redis_service import redis_service
import logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_service.connect()
    yield
    await redis_service.close()



logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title = settings.PROJECT_NAME,
    version = settings.VERSION,
    description = "API Gateway for microservices with proxy support",
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


app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "API Gateway is running", "version": settings.VERSION}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host = "0.0.0.0", port = 8000)