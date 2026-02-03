"""
Fleet Reporting Backend - Main Application Entry Point
"""
from app import app

if __name__ == "__main__":
    import uvicorn
    # Use the app imported from the package
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
