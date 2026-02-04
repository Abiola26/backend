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
if settings.secret_key == "insecure-dev-key-fallback":
    logger.warning("Using default SECRET_KEY! Set SECRET_KEY in environment for production!")
else:
    logger.info("Custom SECRET_KEY loaded")

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
    
    try:
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        logger.info("Database connection established and tables verified")
        
        # Seed initial admin user if no users exist
        from app.database import SessionLocal
        from app.models import User
        from app.crud import create_user
        
        db = SessionLocal()
        try:
            user_count = db.query(User).count()
            if user_count == 0:
                logger.info("No users found in database. Initializing default admin...")
                # Create default admin: admin / admin123
                # In a real production apps, these would come from secret environment variables
                admin_user = create_user(db, username="admin", password="admin123", role="admin")
                logger.warning("**************************************************")
                logger.warning(f"DEFAULT ADMIN CREATED: {admin_user.username} / admin123")
                logger.warning("CHANGE THIS PASSWORD IMMEDIATELY IN PRODUCTION!")
                logger.warning("**************************************************")
            else:
                logger.info(f"Database already initialized with {user_count} users")
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Could not verify database tables on startup: {e}")
        # We don't exit here to allow the app to start and potentially show health check info
    
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
    allow_origins=settings.cors_origins,  # Use the property that parses the string
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
    
    try:
        db = SessionLocal()
        maintenance = db.query(SystemSetting).filter(SystemSetting.key == "MAINTENANCE_MODE").first()
        if maintenance and maintenance.value.lower() == "true":
            # 2. Check if the user is an Admin (Admins can bypass maintenance)
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                try:
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
    except Exception as e:
        # If DB is down during maintenance check, log it but let the request through 
        # (or block if preferred, but letting through is safer for "Up" status)
        logger.error(f"Maintenance check failed: {e}")
    finally:
        if 'db' in locals():
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
