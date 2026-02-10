"""
Fleet Reporting Backend - Main Application Entry Point
"""

# Export the ASGI application instance for WSGI/ASGI servers (gunicorn, uvicorn)
from app.main import app  # re-export the application

if __name__ == "__main__":
    import uvicorn

    # Use the app imported from the package
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
