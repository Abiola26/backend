"""
Application configuration management
Centralizes all configuration variables from environment
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database - with fallback to SQLite for development
    database_url: str = "sqlite:///./fleet.db"
    
    # Security
    secret_key: str | None = None
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    
    # CORS - can be a comma-separated string or list
    allowed_origins: str | list[str] = "http://localhost:3000,http://localhost:5173,http://localhost:5175,https://frontend-psi-one-79.vercel.app"
    
    # Application
    app_name: str = "fras"
    app_version: str = "1.0.0"
    debug: bool = False

    # Email
    mail_username: str | None = None
    mail_password: str | None = None
    mail_from: str | None = None
    mail_port: int = 587
    mail_server: str = "smtp.gmail.com"
    mail_starttls: bool = True
    mail_ssl_tls: bool = False
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "env_file_encoding": "utf-8"
    }
    
    @property
    def cors_origins(self) -> list[str]:
        """Parse allowed_origins into a list"""
        if isinstance(self.allowed_origins, list):
            return self.allowed_origins
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    def __init__(self, **values):
        super().__init__(**values)
        # Fix for Render/Heroku PostgreSQL URL format (postgres:// vs postgresql://)
        if self.database_url and self.database_url.startswith("postgres://"):
            self.database_url = self.database_url.replace("postgres://", "postgresql://", 1)
        if not self.secret_key:
            raise ValueError("SECRET_KEY must be set via environment variable.")
        if not self.mail_username or not self.mail_password or not self.mail_from:
            raise ValueError("Mail credentials (MAIL_USERNAME, MAIL_PASSWORD, MAIL_FROM) must be set.")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
