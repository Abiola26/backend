"""
File upload and processing routes
"""
import logging
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session
import pandas as pd
from io import BytesIO

from app.database import get_db
from app.dependencies import admin_required
from app.models import FleetRecord, User
from app import crud

router = APIRouter(prefix="/files", tags=["File Upload"])
logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {"Date", "Fleet", "Amount"}
ALLOWED_EXTENSIONS = {".csv", ".xlsx"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Map various possible column names to our required names
COLUMN_MAPPING = {
    "date": "Date",
    "transaction date": "Date",
    "transaction_date": "Date",
    "bus": "Fleet",
    "bus_code": "Fleet",
    "bus code": "Fleet",
    "fleet": "Fleet",
    "revenue": "Amount",
    "total": "Amount",
    "amount": "Amount"
}

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
        "errors": [],
        "row_errors": 0,
    }

    for file in files:
        # Validate file extension
        file_ext = "." + (file.filename.lower().split('.')[-1] if '.' in file.filename else '')
        if file_ext not in ALLOWED_EXTENSIONS:
            import_stats["errors"].append(f"{file.filename}: Invalid file type. Only CSV and XLSX are allowed.")
            continue
        
        content = await file.read()
        
        # Validate file size
        if len(content) > MAX_FILE_SIZE:
            import_stats["errors"].append(f"{file.filename}: Size exceeds limit (10MB)")
            continue

        try:
            # Read file based on extension
            if file.filename.lower().endswith(".csv"):
                df = pd.read_csv(BytesIO(content))
            else:
                df = pd.read_excel(BytesIO(content))
        except Exception as e:
            import_stats["errors"].append(f"{file.filename}: Error reading file: {str(e)}")
            continue

        if df.empty:
            import_stats["errors"].append(f"{file.filename}: File is empty")
            continue

        # Normalize column names
        current_cols = {str(c).lower().strip(): c for c in df.columns}
        col_map = {}
        for alias, target in COLUMN_MAPPING.items():
            if alias in current_cols:
                col_map[current_cols[alias]] = target
        
        df = df.rename(columns=col_map)

        # Check for required columns
        missing_cols = REQUIRED_COLUMNS - set(df.columns)
        if missing_cols:
            import_stats["errors"].append(f"{file.filename}: Missing required columns: {', '.join(missing_cols)}")
            continue

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
                import_stats["row_errors"] += 1
                logger.warning(
                    "Skipped row in %s due to error: %s", file.filename, e, exc_info=True
                )
        
        import_stats["files_processed"] += 1
        import_stats["records_imported"] += file_records

    if import_stats["files_processed"] == 0 and import_stats["errors"]:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Import failed: {import_stats['errors']}"
        )

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
    
    # Notify admins about successful upload
    if import_stats["records_imported"] > 0:
        admins = db.query(User).filter(User.role == "admin").all()
        for admin in admins:
            try:
                crud.create_notification(
                    db,
                    title="Data Import Successful",
                    message=f"{import_stats['records_imported']} new records imported from {import_stats['files_processed']} file(s).",
                    type="info",
                    user_id=admin.id
                )
            except Exception as e:
                logger.error(f"Failed to create notification for admin {admin.id}: {e}")

    return {
        "message": "Upload processing complete",
        "stats": import_stats
    }

