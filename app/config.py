"""
Application configuration management
Centralizes all configuration variables from environment
"""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database - with fallback to SQLite for development
    database_url: str = "sqlite:///./fleet.db"
    
    # Security - with default for development (CHANGE IN PRODUCTION!)
    secret_key: str = "dev-secret-key-change-in-production-use-env-variable"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    
    # CORS
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Application
    app_name: str = "fras"
    app_version: str = "1.0.0"
    debug: bool = False

    # Email
    mail_username: str = "user@example.com"
    mail_password: str = "password"
    mail_from: str = "user@example.com"
    mail_port: int = 587
    mail_server: str = "smtp.gmail.com"
    mail_starttls: bool = True
    mail_ssl_tls: bool = False
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "env_file_encoding": "utf-8"
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    settings = Settings()
    
    # Warn if using default secret key
    if settings.secret_key == "dev-secret-key-change-in-production-use-env-variable":
        print("WARNING: Using default SECRET_KEY! Set SECRET_KEY in .env for production!")
    
    # Warn if using SQLite
    if settings.database_url.startswith("sqlite"):
        print("INFO: Using SQLite database for development")
    
    return settings
