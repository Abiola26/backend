"""
File upload and processing routes
"""
import logging
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import pandas as pd
from io import BytesIO
from datetime import datetime

from app.database import get_db
from app.dependencies import admin_required
from app.models import FleetRecord, User, Notification
from app import crud

router = APIRouter(prefix="/files", tags=["File Upload"])
logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {"Date", "Fleet", "Amount"}
ALLOWED_EXTENSIONS = {".csv", ".xlsx"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/upload")
async def upload_files(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(admin_required)
):
    """
    Upload CSV or Excel files and process them
    
    - Accepts multiple files
    - Validates columns
    - Imports data to database
    - Returns import summary
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided"
        )
    
    import_stats = {
        "files_processed": 0,
        "records_imported": 0,
        "errors": []
    }

    for file in files:
        # Validate file extension
        file_ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
        if f".{file_ext}" not in ALLOWED_EXTENSIONS:
            import_stats["errors"].append(f"{file.filename}: Invalid type")
            continue
        
        content = await file.read()
        
        # Validate file size
        if len(content) > MAX_FILE_SIZE:
            import_stats["errors"].append(f"{file.filename}: Size exceeds limit")
            continue

        try:
            # Read file based on extension
            if file.filename.lower().endswith(".csv"):
                df = pd.read_csv(BytesIO(content))
            elif file.filename.lower().endswith(".xlsx"):
                df = pd.read_excel(BytesIO(content))
            else:
                continue # Should not happen due to check above
        except Exception as e:
            logger.error(f"Error reading file {file.filename}: {str(e)}")
            import_stats["errors"].append(f"{file.filename}: Read error - {str(e)}")
            continue

        # Validate required columns
        # Case insensitive check
        df_cols = {c.lower() for c in df.columns}
        req_cols_lower = {c.lower() for c in REQUIRED_COLUMNS}
        
        if not req_cols_lower.issubset(df_cols):
            missing = req_cols_lower - df_cols
            import_stats["errors"].append(f"{file.filename}: Missing columns {missing}")
            continue

        # Map columns to standard names
        col_map = {c: c for c in df.columns} # Identity map fallback
        for c in df.columns:
            if c.lower() == "date": col_map[c] = "Date"
            if c.lower() == "fleet": col_map[c] = "Fleet"
            if c.lower() == "amount": col_map[c] = "Amount"
        
        df = df.rename(columns=col_map)

        # Clean and normalize data
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date
        df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
        df["Fleet"] = df["Fleet"].astype(str).str.strip().str.upper()
        
        # Normalize specific fleet names
        df["Fleet"] = df["Fleet"].replace("2010M", "2010")
        
        # Remove rows with invalid dates
        df = df.dropna(subset=["Date"])

        # Process and store records
        file_records = 0
        for _, row in df.iterrows():
            try:
                record = FleetRecord(
                    date=row["Date"],
                    fleet=row["Fleet"],
                    amount=row["Amount"]
                )
                db.add(record)
                file_records += 1
            except Exception as e:
                # Log specific row errors but don't fail entire file
                continue
        
        import_stats["files_processed"] += 1
        import_stats["records_imported"] += file_records

    try:
        db.commit()
        logger.info(f"Successfully imported {import_stats['records_imported']} fleet records")
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error saving records to database"
        )
    
    if import_stats["files_processed"] == 0 and import_stats["errors"]:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Import failed: {import_stats['errors']}"
        )

    # Notify admins about successful upload
    if import_stats["records_imported"] > 0:
        admins = db.query(User).filter(User.role == "admin").all()
        for admin in admins:
            crud.create_notification(
                db,
                title="Data Import Successful",
                message=f"{import_stats['records_imported']} new records imported from {import_stats['files_processed']} file(s).",
                type="info",
                user_id=admin.id
            )

    return {
        "message": "Upload processing complete",
        "stats": import_stats
    }


