"""Database connection and session management."""

from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from mcp_wordpress.core.config import settings


# Sync engine for migrations (convert asyncpg URL to sync psycopg2 URL)
sync_database_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
sync_engine = create_engine(sync_database_url, echo=settings.debug)

# Async engine for application use (ensure asyncpg URL)
async_database_url = settings.database_url
if "postgresql+asyncpg://" not in async_database_url:
    async_database_url = async_database_url.replace("postgresql://", "postgresql+asyncpg://")

async_engine = create_async_engine(
    async_database_url,
    echo=settings.debug,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600
)

# Async session factory
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


def create_db_and_tables():
    """Create database tables."""
    SQLModel.metadata.create_all(sync_engine)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()