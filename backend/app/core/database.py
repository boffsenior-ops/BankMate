import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import settings

# If we are running outside docker, we might want to connect to localhost. 
# We'll use database_url inside docker and database_url_local when running locally for alembic.
DB_URL = settings.database_url if os.getenv("DOCKER_ENV") else settings.database_url_local

engine = create_async_engine(
    DB_URL,
    echo=False,
    future=True
)

async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)

Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
