"""
Database configuration and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Generator

from app.config import get_settings

settings = get_settings()

# Create database engine with connection pooling
# Note: Lowered pool sizes for compatibility with free-tier Postgres limits
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=3,         # Reduced from 5
    max_overflow=2,      # Reduced from 10
    pool_recycle=300,    # Close connections after 5 mins to prevent stale links
    echo=settings.debug  # Log SQL queries in debug mode
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for declarative models
Base = declarative_base()


def get_db() -> Generator:
    """
    Database dependency for FastAPI routes
    Provides a database session and ensures it's closed after use
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
