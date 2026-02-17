"""
Async Database Session Management

Provides async SQLAlchemy engine and session management.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from backend.core.config import settings
from backend.core.exceptions import DatabaseError


# Global engine instance
_engine: Optional[AsyncEngine] = None
_session_factory: Optional[sessionmaker] = None


def create_database_engine() -> AsyncEngine:
    """
    Create async database engine.
    
    Uses asyncpg for PostgreSQL with connection pooling.
    """
    global _engine
    
    if _engine is not None:
        return _engine
    
    try:
        # Create async engine with appropriate pool settings
        # Note: When using NullPool, we can't use pool_size/max_overflow/pool_pre_ping
        _engine = create_async_engine(
            settings.database_url,
            echo=False,  # Set to True for SQL debugging
            poolclass=NullPool,  # Use NullPool for asyncpg compatibility
        )
        
        return _engine
        
    except Exception as e:
        raise DatabaseError(
            f"Failed to create database engine: {str(e)}",
            details={"database_url": settings.database_url.split("@")[-1] if "@" in settings.database_url else "unknown"}
        )


def get_session_factory() -> sessionmaker:
    """
    Get or create session factory.
    
    Returns:
        SQLAlchemy async session maker
    """
    global _session_factory, _engine
    
    if _engine is None:
        _engine = create_database_engine()
    
    if _session_factory is None:
        _session_factory = sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    
    return _session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database session.
    
    Yields:
        Async SQLAlchemy session
        
    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db_session)):
            ...
    """
    factory = get_session_factory()
    
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions.
    
    Usage:
        async with get_db_context() as session:
            result = await session.execute(...)
    """
    factory = get_session_factory()
    
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_database() -> None:
    """
    Initialize database tables.
    
    Creates all tables if they don't exist.
    For production, use Alembic migrations instead.
    """
    from backend.db.models import Base
    
    engine = create_database_engine()
    
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    # Dispose engine (will be recreated on next use)
    await engine.dispose()


async def close_database() -> None:
    """
    Close database connections and dispose engine.
    
    Call this on application shutdown.
    """
    global _engine, _session_factory
    
    if _engine is not None:
        await _engine.dispose()
        _engine = None
    
    _session_factory = None


async def check_database_connection() -> bool:
    """
    Check database connectivity.
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        engine = create_database_engine()
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception:
        return False
