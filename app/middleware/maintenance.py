import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from jose import jwt
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.database import SessionLocal
from app.models import SystemSetting, User

logger = logging.getLogger("app")
settings = get_settings()

PUBLIC_PATH_PREFIXES = (
    "/auth",
    "/docs",
    "/openapi.json",
    "/health",
)


class MaintenanceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        """
        Middleware to check if the system is in maintenance mode.
        Allows preflight requests, public paths, and admin users to bypass.
        """
        # 1. Always allow preflight requests (needed for CORS)
        if request.method == "OPTIONS":
            return await call_next(request)

        # 2. Skip check for root and public paths
        if request.url.path == "/" or any(
            request.url.path.startswith(prefix) for prefix in PUBLIC_PATH_PREFIXES
        ):
            return await call_next(request)

        db = None
        try:
            db = SessionLocal()
            maintenance = (
                db.query(SystemSetting)
                .filter(SystemSetting.key == "MAINTENANCE_MODE")
                .first()
            )

            if maintenance and maintenance.value.lower() == "true":
                # Check if user is admin (admins bypass maintenance)
                auth_header = request.headers.get("Authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header.split(" ")[1]
                    try:
                        payload = jwt.decode(
                            token, settings.secret_key, algorithms=[settings.algorithm]
                        )
                        username = payload.get("sub")
                        if username:
                            user = (
                                db.query(User).filter(User.username == username).first()
                            )
                            if user and user.role == "admin":
                                return await call_next(request)
                    except Exception:
                        logger.warning(
                            "Invalid or expired token during maintenance bypass attempt"
                        )

                # Block non-admin users
                return JSONResponse(
                    status_code=503,
                    content={
                        "detail": "System is currently undergoing maintenance. Please try again later."
                    },
                )
        except Exception as e:
            logger.error(f"Maintenance check failed: {e}")
        finally:
            if db:
                db.close()

        return await call_next(request)
