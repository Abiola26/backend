"""
Main Application Factory
Aggregates routers, middleware, and lifespan events.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.routers import (
    auth_routes,
    fleet_routes,
    file_routes,
    analytics_routes,
    audit_routes,
    settings_routes,
    notification_routes,
)
from app.utils.limiter import init_limiter
from app.utils.logging_config import setup_logging
from app.lifespan import lifespan
from app.middleware.maintenance import maintenance_middleware

settings = get_settings()

# Initialize logging before app creation
setup_logging(debug=settings.debug)

def create_app() -> FastAPI:
    """
    Creates and configures the FastAPI application instance.
    """
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Fleet Reporting and Analytics System API",
        lifespan=lifespan,
    )

    # 1. Initialize Rate Limiter
    init_limiter(app)

    # 2. Register Custom Middlewares
    # Note: Middlewares are executed in the order they are added (Starlette logic).
    # 'http' generic middlewares added via @app.middleware are processed first.
    app.middleware("http")(maintenance_middleware)
    
    # 3. Register Standard Middlewares
    # CORSMiddleware is added last so it is the "outermost" layer.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 4. Include Domain Routers
    app.include_router(auth_routes.router)
    app.include_router(fleet_routes.router)
    app.include_router(file_routes.router)
    app.include_router(analytics_routes.router)
    app.include_router(audit_routes.router)
    app.include_router(settings_routes.router)
    app.include_router(notification_routes.router)

    # 5. Application-level endpoints
    @app.get("/", tags=["System"])
    def root():
        """Root endpoint to check service status"""
        return {
            "message": "Fleet Reporting Backend is running",
            "version": settings.app_version,
            "status": "healthy",
        }

    @app.get("/health", tags=["System"])
    def health_check():
        """Health check endpoint for monitoring systems"""
        return {
            "status": "healthy",
            "service": settings.app_name,
            "version": settings.app_version,
        }

    @app.get("/debug/cors", tags=["Debug"])
    def debug_cors():
        """Debug endpoint to check CORS configuration"""
        return {
            "cors_origins": settings.cors_origins,
            "raw_allowed_origins": settings.allowed_origins,
        }

    return app

# The exported 'app' instance used by the ASGI server (uvicorn/gunicorn)
app = create_app()
