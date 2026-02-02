from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import SystemSetting
from app.schemas import SystemSettingBase, SystemSettingOut
from app.dependencies import admin_required
from app import crud

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("/", response_model=List[SystemSettingOut])
def get_settings(db: Session = Depends(get_db)):
    """Get all system settings"""
    return db.query(SystemSetting).all()

@router.put("/{key}", response_model=SystemSettingOut)
def update_setting(
    key: str, 
    setting: SystemSettingBase, 
    db: Session = Depends(get_db),
    _ = Depends(admin_required)
):
    """Update a system setting (Admin only)"""
    db_setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if not db_setting:
        # Create if it doesn't exist
        db_setting = SystemSetting(key=key, value=setting.value, description=setting.description)
        db.add(db_setting)
    else:
        db_setting.value = setting.value
        if setting.description:
            db_setting.description = setting.description
    
    db.commit()
    db.refresh(db_setting)
    return db_setting
