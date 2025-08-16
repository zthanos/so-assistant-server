"""Database connection management.

This module provides utilities for managing database connections, sessions, and transactions.
It follows the repository pattern and provides a clean interface for database operations.
"""
import os
import logging
import asyncio
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager, asynccontextmanager
from typing import Generator, AsyncGenerator, Optional, Callable, TypeVar, Any

# Type variables for generic functions
T = TypeVar('T')

# Get database URL from environment variable or use default
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./so_assistant.db")
ASYNC_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL", DATABASE_URL.replace('sqlite:///', 'sqlite+aiosqlite:///'))

# Create SQLAlchemy engines
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,  # Enable connection health checks
    pool_recycle=3600,   # Recycle connections after 1 hour
    echo=os.getenv("SQL_ECHO", "false").lower() == "true"  # Set to True for SQL logging
)

# Create async engine if using a compatible database
try:
    async_engine = create_async_engine(
        ASYNC_DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true"
    )
    has_async_support = True
except ImportError:
    has_async_support = False
    logging.warning("Async database support not available. Using synchronous database operations only.")

# Create session factories
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

if has_async_support:
    AsyncSessionLocal = async_sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=async_engine,
        expire_on_commit=False
    )

# Create base class for declarative models
Base = declarative_base()

# SQLite specific configuration
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas for better performance and data integrity."""
    if DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

def init_db() -> None:
    """Initialize the database by creating all tables."""
    Base.metadata.create_all(bind=engine)
    logging.info("Database tables created.")

async def async_init_db() -> None:
    """Initialize the database asynchronously by creating all tables."""
    if has_async_support:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logging.info("Database tables created asynchronously.")
    else:
        # Fall back to synchronous initialization
        init_db()

def get_db() -> Generator[Session, None, None]:
    """Get a database session.
    
    This function is used as a FastAPI dependency to get a database session.
    It ensures that the session is closed after use, even if an exception occurs.
    
    Yields:
        Session: A SQLAlchemy session.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as ex:
        logging.error(f"Error in database session: {ex}")
        print(ex)
        db.rollback()
        raise
    finally:
        db.close()

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session.
    
    This function is used as a FastAPI dependency to get an async database session.
    It ensures that the session is closed after use, even if an exception occurs.
    
    Yields:
        AsyncSession: An async SQLAlchemy session.
    """
    if not has_async_support:
        raise RuntimeError("Async database support not available")
        
    async_session = AsyncSessionLocal()
    try:
        yield async_session
    except Exception:
        await async_session.rollback()
        raise
    finally:
        await async_session.close()

@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Get a database session using a context manager.
    
    This function is used when a context manager is needed instead of a FastAPI dependency.
    
    Yields:
        Session: A SQLAlchemy session.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

@asynccontextmanager
async def get_async_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session using a context manager.
    
    This function is used when an async context manager is needed instead of a FastAPI dependency.
    
    Yields:
        AsyncSession: An async SQLAlchemy session.
    """
    if not has_async_support:
        raise RuntimeError("Async database support not available")
        
    async_session = AsyncSessionLocal()
    try:
        yield async_session
    except Exception:
        await async_session.rollback()
        raise
    finally:
        await async_session.close()

def get_db_session() -> Session:
    """Get a database session.
    
    This function is used when a simple session is needed without a context manager.
    The caller is responsible for closing the session.
    
    Returns:
        Session: A SQLAlchemy session.
    """
    return SessionLocal()

def get_async_db_session() -> AsyncSession:
    """Get an async database session.
    
    This function is used when a simple async session is needed without a context manager.
    The caller is responsible for closing the session.
    
    Returns:
        AsyncSession: An async SQLAlchemy session.
    """
    if not has_async_support:
        raise RuntimeError("Async database support not available")
    return AsyncSessionLocal()

def run_in_transaction(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Run a function in a database transaction.
    
    This function creates a database session, calls the provided function with the session
    and any additional arguments, and commits the transaction if successful.
    
    Args:
        func: The function to run in a transaction.
        *args: Positional arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.
        
    Returns:
        The result of the function call.
    """
    with get_db_context() as session:
        result = func(session, *args, **kwargs)
        session.commit()
        return result

async def run_in_async_transaction(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Run a function in an async database transaction.
    
    This function creates an async database session, calls the provided function with the session
    and any additional arguments, and commits the transaction if successful.
    
    Args:
        func: The async function to run in a transaction.
        *args: Positional arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.
        
    Returns:
        The result of the function call.
    """
    if not has_async_support:
        raise RuntimeError("Async database support not available")
        
    async with get_async_db_context() as session:
        result = await func(session, *args, **kwargs)
        await session.commit()
        return result