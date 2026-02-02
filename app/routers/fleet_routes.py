"""
Fleet record management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas import FleetRecordBase, FleetRecordOut
from app.database import get_db
from app import crud
from app.dependencies import admin_required
from app.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/fleet", tags=["Fleet Records"])


@router.post("/", response_model=FleetRecordOut, status_code=status.HTTP_201_CREATED)
def create_record(
    data: FleetRecordBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new fleet record
    
    Requires authentication
    """
    return crud.create_fleet_record(db, data)


@router.get("/", response_model=list[FleetRecordOut])
def get_records(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all fleet records with pagination
    
    Requires authentication
    """
    return crud.get_fleet_records(db, skip, limit)


@router.delete("/batch", status_code=status.HTTP_200_OK)
def delete_records_batch(
    start_date: str = None, # Using str to allow easy parsing or optionality
    end_date: str = None,
    fleet: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required)
):
    """
    Delete multiple records based on filters.
    """
    from datetime import datetime
    
    s_date = None
    e_date = None
    
    if start_date:
        try:
            s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
             raise HTTPException(status_code=400, detail="Invalid start_date format (YYYY-MM-DD)")
            
    if end_date:
        try:
             e_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
             raise HTTPException(status_code=400, detail="Invalid end_date format (YYYY-MM-DD)")

    count = crud.delete_records_batch(db, s_date, e_date, fleet)
    
    # Log action
    crud.create_audit_log(
        db, 
        current_user.id, 
        current_user.username, 
        "DELETE_BATCH", 
        f"Count: {count}, Filters: start={start_date}, end={end_date}, fleet={fleet}"
    )
    
    return {"message": f"Successfully deleted {count} records", "count": count}


@router.delete("/{record_id}")
def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required)
):
    """
    Delete a fleet record by ID
    
    Requires admin role
    """
    deleted = crud.delete_record(db, record_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Record with ID {record_id} not found"
        )
        
    crud.create_audit_log(
        db, 
        current_user.id, 
        current_user.username, 
        "DELETE_RECORD", 
        f"ID: {record_id}"
    )
        
    return {"message": "Record deleted successfully", "id": record_id}
