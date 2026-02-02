#!/usr/bin/env python
"""
Quick start script for FRAS Backend
This script checks dependencies and starts the application
"""
import sys
import subprocess
import os
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

def check_env_file():
    """Check if .env file exists"""
    if not os.path.exists('.env'):
        print("⚠️  .env file not found!")
        print("📝 Please copy .env.example to .env and configure it")
        print("\n   Run: cp .env.example .env (Linux/Mac)")
        print("   Or:  copy .env.example .env (Windows)")
        return False
    return True

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import pydantic
        import pydantic_settings
        print("Dependencies are installed")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e.name}")
        print("\n📦 Please install dependencies:")
        print("   pip install -r requirements.txt")
        return False

def main():
    print("=" * 60)
    print("  Fleet Reporting and Analytics System (FRAS)")
    print("  Backend Startup Script")
    print("=" * 60)
    print()
    
    # Check environment file
    if not check_env_file():
        sys.exit(1)
    
    # Load environment variables explicitly
    if load_dotenv:
        load_dotenv()
        print("Loaded environment variables from .env")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    print("Starting FRAS Backend...")
    print("API will be available at: http://localhost:8000")
    print("API docs will be available at: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server\n")
    print("=" * 60)
    print()
    
    # Start uvicorn
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "main:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000"
        ])
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")
        sys.exit(0)

if __name__ == "__main__":
    main()
