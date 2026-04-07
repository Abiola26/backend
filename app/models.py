"""
Database models
"""
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, Date, DateTime, Float, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


def _now():
    """Return current UTC time (timezone-aware). Used as column defaults."""
    return datetime.now(timezone.utc)


class User(Base):
    """User model for authentication and authorization."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user")  # "admin" or "user"
    account_id = Column(String, unique=True, index=True, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    last_login = Column(DateTime(timezone=True), nullable=True)
    is_locked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=_now)


class FleetRecord(Base):
    """Fleet record model for storing fleet data."""
    __tablename__ = "fleet_records"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    fleet = Column(String, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_now)


class AuditLog(Base):
    """Audit log model for tracking user actions."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    username = Column(String, nullable=True)
    action = Column(String, nullable=False, index=True)
    details = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=_now)


class SystemSetting(Base):
    """System settings for configurable business logic."""
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    value = Column(String, nullable=False)
    description = Column(String, nullable=True)


class Notification(Base):
    """Notification model for system alerts."""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=True)  # None = broadcast to all
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    type = Column(String, default="info")  # info | warning | success | error
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=_now)
