from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from src.core import config
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker

from src.models.model import User



engine = create_async_engine(
    url = config.DATABASE_URL,
    echo = True
)

async def get_session() -> AsyncSession:
    Session = sessionmaker(
        bind = engine,
        class_= AsyncSession,
        expire_on_commit = False
    )
    async with Session() as session:
        yield session