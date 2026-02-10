"""
Main Application Factory
Aggregates routers, middleware, and lifespan events.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.lifespan import lifespan
from app.routers import (
    analytics_routes,
    audit_routes,
    auth_routes,
    file_routes,
    fleet_routes,
    notification_routes,
    settings_routes,
)
from app.utils.limiter import init_limiter
from app.utils.logging_config import setup_logging

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

    # 2. Register Middlewares
    # Note: Middlewares are executed in REVERSE order of addition (LIFO).
    # The last one added is the "outermost" layer.

    # Inner: Maintenance logic
    from app.middleware.maintenance import MaintenanceMiddleware

    app.add_middleware(MaintenanceMiddleware)

    # Outer: CORS headers (must be outermost to catch exceptions from inner layers)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 4. Global Exception Handlers (Backup CORS for errors)
    from fastapi import HTTPException
    from fastapi.responses import JSONResponse

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        response = JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=exc.headers,
        )
        # Add CORS headers manually to error responses as a fallback
        origin = request.headers.get("origin")
        if origin and (origin in settings.cors_origins or "*" in settings.cors_origins):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
        elif "*" in settings.cors_origins:
            response.headers["Access-Control-Allow-Origin"] = "*"

        return response

    # 5. Include Domain Routers
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

    # Fallback HTTP middleware to ensure CORS headers are always present
    @app.middleware("http")
    async def ensure_cors_headers(request: Request, call_next):
        # Let CORSMiddleware handle most cases; this is a fallback for proxies/errors
        if request.method == "OPTIONS":
            from fastapi.responses import Response

            origin = request.headers.get("origin")
            headers = {}
            if "*" in settings.cors_origins:
                headers["Access-Control-Allow-Origin"] = "*"
            elif origin and origin in settings.cors_origins:
                headers["Access-Control-Allow-Origin"] = origin
                headers["Access-Control-Allow-Credentials"] = "true"
            headers["Access-Control-Allow-Methods"] = ", ".join(["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
            headers["Access-Control-Allow-Headers"] = "*"
            return Response(status_code=204, headers=headers)

        response = await call_next(request)
        origin = request.headers.get("origin")
        if "*" in settings.cors_origins:
            response.headers["Access-Control-Allow-Origin"] = "*"
        elif origin and origin in settings.cors_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
        return response

    return app


# The exported 'app' instance used by the ASGI server (uvicorn/gunicorn)
app = create_app()
