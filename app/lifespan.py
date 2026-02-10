import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.crud import create_user
from app.database import Base, SessionLocal, engine
from app.models import User

logger = logging.getLogger("app")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events (Startup/Shutdown).
    Handles database initialization and essential seeding.
    """
    logger.info(f"--- Starting {settings.app_name} v{settings.app_version} ---")

    # Log configuration status
    if settings.secret_key == "insecure-dev-key-fallback":
        logger.warning(
            "Using default SECRET_KEY! Set SECRET_KEY in environment for production!"
        )
    else:
        logger.info("Custom SECRET_KEY loaded")

    if settings.database_url.startswith("sqlite"):
        logger.info("Using SQLite database for development")
    else:
        db_type = settings.database_url.split(":")[0]
        logger.info(f"Using {db_type} database")

    try:
        # Create tables if they don't exist
        # Note: In production, migrations (Alembic) are preferred
        Base.metadata.create_all(bind=engine)
        logger.info("Database connection established and tables verified")

        # Ensure default admin user exists
        db = SessionLocal()
        try:
            admin_user = db.query(User).filter(User.username == "admin").first()
            if not admin_user:
                logger.info("Admin user not found. Initializing default admin...")
                # Create default admin: admin / admin123
                admin_user = create_user(
                    db, username="admin", password="admin123", role="admin"
                )
                logger.warning("**************************************************")
                logger.warning(
                    f"DEFAULT ADMIN CREATED: {admin_user.username} / admin123"
                )
                logger.warning("CHANGE THIS PASSWORD IMMEDIATELY IN PRODUCTION!")
                logger.warning("**************************************************")
            else:
                logger.info("Admin user already exists")
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Could not verify database tables on startup: {e}")

    yield

    logger.info("Shutting down Fleet Reporting Backend...")
