from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import admin_required
from app.models import SystemSetting
from app.schemas import SystemSettingBase, SystemSettingOut

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
    _=Depends(admin_required),
):
    """Update a system setting (Admin only)"""
    db_setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if not db_setting:
        # Create if it doesn't exist
        db_setting = SystemSetting(
            key=key, value=setting.value, description=setting.description
        )
        db.add(db_setting)
    else:
        db_setting.value = setting.value
        if setting.description:
            db_setting.description = setting.description

    db.commit()
    db.refresh(db_setting)
    return db_setting


@router.post("/maintenance/toggle")
def toggle_maintenance_mode(db: Session = Depends(get_db), _=Depends(admin_required)):
    """Toggle system maintenance mode (Admin only)"""
    db_setting = (
        db.query(SystemSetting).filter(SystemSetting.key == "MAINTENANCE_MODE").first()
    )
    if not db_setting:
        db_setting = SystemSetting(
            key="MAINTENANCE_MODE", value="true", description="System Maintenance Mode"
        )
        db.add(db_setting)
    else:
        db_setting.value = "false" if db_setting.value.lower() == "true" else "true"

    db.commit()
    return {"maintenance_mode": db_setting.value}


@router.post("/backup")
def trigger_backup(_=Depends(admin_required)):
    """Trigger a manual database backup (Admin only)"""
    from app.utils.backup import run_backup

    success = run_backup()
    if success:
        return {"status": "success", "message": "Backup created successfully"}
    else:
        raise HTTPException(
            status_code=500, detail="Backup failed. Check logs for details."
        )
