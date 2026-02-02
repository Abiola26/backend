"""
CRUD operations for database models
"""
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from .models import User, FleetRecord, AuditLog
from .auth import get_password_hash, verify_password
from .schemas import FleetRecordBase
from .utils import generate_account_id


def create_user(db: Session, username: str, password: str, role: str = "user", email: str = None) -> User:
    """
    Create a new user in the database
    
    Args:
        db: Database session
        username: Username for the new user
        password: Plain text password
        role: User role (default: "user")
        email: Optional email address
        
    Returns:
        Created User object
    """
    user = User(
        username=username,
        email=email,
        hashed_password=get_password_hash(password),
        role=role,
        account_id=generate_account_id(role)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_fleet_record(db: Session, data: FleetRecordBase) -> FleetRecord:
    """
    Create a new fleet record
    
    Args:
        db: Database session
        data: Fleet record data
        
    Returns:
        Created FleetRecord object
    """
    record = FleetRecord(**data.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_fleet_records(db: Session, skip: int = 0, limit: int = 50) -> list[FleetRecord]:
    """
    Get fleet records with pagination
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of FleetRecord objects
    """
    return db.query(FleetRecord).offset(skip).limit(limit).all()


def delete_record(db: Session, record_id: int) -> Optional[FleetRecord]:
    """
    Delete a fleet record by ID
    
    Args:
        db: Database session
        record_id: ID of the record to delete
        
    Returns:
        Deleted FleetRecord object if found, None otherwise
    """
    record = db.query(FleetRecord).filter(FleetRecord.id == record_id).first()
    if record:
        db.delete(record)
        db.commit()
    return record


def delete_records_batch(db: Session, start_date: Optional[date] = None, end_date: Optional[date] = None, fleet: Optional[str] = None) -> int:
    """
    Delete fleet records making the specific filters
    """
    query = db.query(FleetRecord)
    if start_date:
        query = query.filter(FleetRecord.date >= start_date)
    if end_date:
        query = query.filter(FleetRecord.date <= end_date)
    if fleet and fleet != 'All':
        query = query.filter(FleetRecord.fleet == fleet)
    
    deleted_count = query.delete(synchronize_session=False)
    db.commit()
    return deleted_count


def create_audit_log(db: Session, user_id: int, username: str, action: str, details: str = None):
    """
    Create an audit log entry
    """
    log = AuditLog(
        user_id=user_id,
        username=username,
        action=action,
        details=details
    )
    db.add(log)
    db.commit()
    return log

def create_notification(db: Session, title: str, message: str, type: str = "info", user_id: int = None):
    """
    Create a system notification
    """
    from .models import Notification
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=type
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif
