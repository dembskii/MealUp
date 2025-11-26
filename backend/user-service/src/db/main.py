from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from src.core.config import settings
import logging

logger = logging.getLogger(__name__)

engine: AsyncEngine = create_async_engine(
    url=settings.USER_DATABASE_URL,
    echo = False,
    future = True,
    pool_pre_ping = True
)


async def get_session() -> AsyncSession:
    """Get database session"""
    async_session = sessionmaker(
        bind = engine,
        class_ = AsyncSession,
        expire_on_commit = False
    )
    async with async_session() as session:
        yield session