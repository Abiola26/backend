"""
Fleet Reporting Backend - App Package
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, engine
from app.routers import auth_routes, fleet_routes, file_routes, analytics_routes, audit_routes, settings_routes, notification_routes
from app.utils.limiter import init_limiter
from app.utils.logging_config import setup_logging

settings = get_settings()

# Configure logging early
setup_logging(debug=settings.debug)
logger = logging.getLogger("app")

# Log configuration status after logger is ready
if settings.secret_key == "dev-secret-key-change-in-production-use-env-variable":
    logger.warning("Using default SECRET_KEY! Set SECRET_KEY in .env for production!")

if settings.database_url.startswith("sqlite"):
    logger.info("Using SQLite database for development")
else:
    # Log database type without exposing credentials
    db_type = settings.database_url.split(":")[0]
    logger.info(f"Using {db_type} database")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(f"--- Starting {settings.app_name} v{settings.app_version} ---")
    
    # Optional: Run migrations or create tables
    # If using Alembic primarily, you might want to comment out create_all
    Base.metadata.create_all(bind=engine)
    logger.info("Database connection established and tables verified")
    
    yield
    # Shutdown
    logger.info("Shutting down Fleet Reporting Backend...")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Fleet Reporting and Analytics System API",
    lifespan=lifespan
)

# Initialize Limiter
init_limiter(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def check_maintenance_mode(request, call_next):
    # 1. Skip check for critical infrastructure routes
    if request.url.path in ["/", "/health", "/auth/token", "/auth/signup", "/docs", "/openapi.json"]:
        return await call_next(request)
        
    # Check DB for maintenance mode
    from app.database import SessionLocal
    from app.models import SystemSetting, User
    from jose import jwt
    from fastapi.responses import JSONResponse
    
    db = SessionLocal()
    try:
        maintenance = db.query(SystemSetting).filter(SystemSetting.key == "MAINTENANCE_MODE").first()
        if maintenance and maintenance.value.lower() == "true":
            # 2. Check if the user is an Admin (Admins can bypass maintenance)
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                try:
                    from jose import jwt
                    from app.config import get_settings
                    config = get_settings()
                    payload = jwt.decode(token, config.secret_key, algorithms=[config.algorithm])
                    username = payload.get("sub")
                    if username:
                        user = db.query(User).filter(User.username == username).first()
                        if user and user.role == "admin":
                            # Admin bypasses maintenance
                            return await call_next(request)
                except Exception:
                    pass # Token invalid, proceed to block
            
            # 3. Block standard users
            return JSONResponse(
                status_code=503,
                content={"detail": "System is currently undergoing maintenance. Please try again later."}
            )
    finally:
        db.close()
        
    return await call_next(request)

# Include routers
app.include_router(auth_routes.router)
app.include_router(fleet_routes.router)
app.include_router(file_routes.router)
app.include_router(analytics_routes.router)
app.include_router(audit_routes.router)
app.include_router(settings_routes.router)
app.include_router(notification_routes.router)



@app.get("/", tags=["Root"])
def root():
    """Root endpoint"""
    return {
        "message": "Fleet Reporting Backend is running",
        "version": settings.app_version,
        "status": "healthy"
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version
    }
