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
    
    # Security
    secret_key: str = "insecure-dev-key-fallback"
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

    def __init__(self, **values):
        super().__init__(**values)
        # Fix for Render/Heroku PostgreSQL URL format (postgres:// vs postgresql://)
        if self.database_url and self.database_url.startswith("postgres://"):
            self.database_url = self.database_url.replace("postgres://", "postgresql://", 1)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
