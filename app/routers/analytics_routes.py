"""
Analytics and Reporting Routes
"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import FleetRecord, User
from app.auth import get_current_user
from app.schemas import AnalyticsResponse, FilterOptions, DashboardStats
from app.utils import DataProcessor, ReportGenerator

router = APIRouter(prefix="/analytics", tags=["Analytics & Reporting"])


def get_filtered_query(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    fleets: Optional[list[str]] = Query(None),
    limit: Optional[int] = None
):
    """Helper to apply filters to fleet query"""
    query = db.query(FleetRecord)
    
    if start_date:
        query = query.filter(FleetRecord.date >= start_date)
    if end_date:
        query = query.filter(FleetRecord.date <= end_date)
    if fleets:
        query = query.filter(FleetRecord.fleet.in_(fleets))
        
    query = query.order_by(FleetRecord.date.desc()) # Show newest first
    
    if limit:
        query = query.limit(limit)
        
    return query


@router.get("/summary", response_model=AnalyticsResponse)
def get_analytics_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    fleets: Optional[list[str]] = Query(None),
    limit: Optional[int] = None, # No limit by default for full report
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive analytics summary including records (Heavier payload)
    """
    query = get_filtered_query(db, start_date, end_date, fleets, limit=limit)
    records = query.all()
    
    # We might want to re-sort for processing if needed, but DataProcessor handles it
    return DataProcessor.process_analytics(records)


@router.get("/dashboard-stats", response_model=DashboardStats)
def get_dashboard_stats(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    fleets: Optional[list[str]] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Highly optimized endpoint for Dashboard KPI cards.
    Uses direct SQL aggregation for maximum performance.
    """
    base_query = get_filtered_query(db, start_date, end_date, fleets)
    
    # CLEAR ORDERING to avoid SQL errors during aggregation
    # (Because get_filtered_query adds order_by(date))
    base_query = base_query.order_by(None)
    
    # 1. Total Revenue & Count
    stats = base_query.with_entities(
        func.sum(FleetRecord.amount).label("total_amount"),
        func.count(FleetRecord.id).label("total_count")
    ).first()
    
    total_revenue = stats.total_amount or 0
    total_records = stats.total_count or 0
    average_trip_revenue = total_revenue / total_records if total_records > 0 else 0
    
    # 2. Top Performing Fleet
    # SELECT fleet, SUM(amount) as s FROM records GROUP BY fleet ORDER BY s DESC LIMIT 1
    top_fleet_query = base_query.with_entities(
        FleetRecord.fleet,
        func.sum(FleetRecord.amount).label("fleet_total")
    ).group_by(FleetRecord.fleet).order_by(func.sum(FleetRecord.amount).desc()).limit(1).first()
    
    top_performing_fleet = top_fleet_query.fleet if top_fleet_query else "N/A"
    
    # 3. Sophisticated Predictive Revenue (Weighted Trend Analysis)
    # Strategy: Look at last 14 days, give more weight to recent days
    all_dates = db.query(FleetRecord.date, func.sum(FleetRecord.amount)).group_by(FleetRecord.date).order_by(FleetRecord.date.desc()).limit(14).all()
    
    if all_dates:
        total_weight = 0
        weighted_sum = 0
        # Most recent date has highest weight
        for i, (dt, daily_total) in enumerate(all_dates):
            weight = 14 - i # 14 for newest, 1 for oldest
            weighted_sum += daily_total * weight
            total_weight += weight
            
        # Predicted revenue for "Tomorrow"
        predicted_revenue = (weighted_sum / total_weight) if total_weight > 0 else 0
        
        # Growth indicator (comparison)
        # If today > weighted average, trend is up
    else:
        predicted_revenue = 0

    return DashboardStats(
        total_revenue=total_revenue,
        total_records=total_records,
        top_performing_fleet=top_performing_fleet,
        average_trip_revenue=average_trip_revenue,
        predicted_revenue=predicted_revenue
    )


from app.schemas import ChartResponse, ChartDataPoint

@router.get("/charts", response_model=ChartResponse)
def get_analytics_charts(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    fleets: Optional[list[str]] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Optimized endpoint for analytics charts.
    Returns pre-aggregated data to avoid sending large payloads.
    """
    base_query = get_filtered_query(db, start_date, end_date, fleets)
    base_query = base_query.order_by(None) # Clear ordering for aggregation

    # 1. Revenue Trend (Daily)
    # Group by Date
    trend_query = base_query.with_entities(
        FleetRecord.date,
        func.sum(FleetRecord.amount).label("total")
    ).group_by(FleetRecord.date).order_by(FleetRecord.date)
    
    revenue_trend = [
        ChartDataPoint(label=str(r.date), value=r.total) 
        for r in trend_query.all()
    ]

    # 2. Revenue by Fleet (Pie & Bar)
    # Group by Fleet
    fleet_query = base_query.with_entities(
        FleetRecord.fleet,
        func.sum(FleetRecord.amount).label("total")
    ).group_by(FleetRecord.fleet).order_by(func.sum(FleetRecord.amount).desc())
    
    fleet_data = fleet_query.all()
    
    revenue_by_fleet = [
        ChartDataPoint(label=r.fleet, value=r.total)
        for r in fleet_data
    ]
    
    # Top Fleets is just the same data, sorted (which it already is)
    top_fleets = revenue_by_fleet[:15] # Limit to top 15

    # 3. Anomalies
    # We need the full record set for anomaly detection
    records = base_query.all()
    from app.utils import DataProcessor
    analytics = DataProcessor.process_analytics(records)
    anomalies = analytics.anomalies

    return ChartResponse(
        revenue_trend=revenue_trend,
        revenue_by_fleet=revenue_by_fleet,
        top_fleets=top_fleets,
        anomalies=anomalies
    )


@router.get("/filters", response_model=FilterOptions)
def get_filter_options(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get available filter options (date range, fleet list)"""
    # Get distinct fleets
    fleets = [r[0] for r in db.query(FleetRecord.fleet).distinct().all()]
    
    # Get date range
    min_date = db.query(func.min(FleetRecord.date)).scalar()
    max_date = db.query(func.max(FleetRecord.date)).scalar()
    
    return FilterOptions(
        fleets=sorted(fleets),
        min_date=min_date,
        max_date=max_date
    )


@router.get("/download/excel")
def download_excel_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    fleets: Optional[list[str]] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download analytics report as Excel"""
    query = get_filtered_query(db, start_date, end_date, fleets)
    records = query.all()
    analytics = DataProcessor.process_analytics(records)
    
    excel_file = ReportGenerator.generate_excel(analytics)
    
    filename = f"Fleet_Report_{date.today()}.xlsx"
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# @router.get("/download/pdf")
# def download_pdf_report(
#     start_date: Optional[date] = None,
#     end_date: Optional[date] = None,
#     fleets: Optional[list[str]] = Query(None),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """Download analytics report as PDF"""
#     query = get_filtered_query(db, start_date, end_date, fleets)
#     records = query.all()
#     analytics = DataProcessor.process_analytics(records)
#     
#     pdf_file = ReportGenerator.generate_pdf(analytics)
#     
#     filename = f"Fleet_Report_{date.today()}.pdf"
#     return StreamingResponse(
#         pdf_file,
#         media_type="application/pdf",
#         headers={"Content-Disposition": f"attachment; filename={filename}"}
#     )


@router.post("/email-report")
async def email_report(
    email: str = Query(None, description="Recipient email (defaults to current user)"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    fleets: Optional[list[str]] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate and email the analytics report (PDF & Excel)
    - Sends to logged-in user or specified email
    """
    from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
    from app.config import get_settings
    
    settings = get_settings()
    
    # Generate reports
    query = get_filtered_query(db, start_date, end_date, fleets)
    records = query.all()
    analytics = DataProcessor.process_analytics(records)
    
    pdf_io = ReportGenerator.generate_pdf(analytics)
    xlsx_io = ReportGenerator.generate_excel(analytics)
    
    today = date.today()
    
    # Prepare attachments
    # fastapi-mail expects file paths or UploadFile, but for in-memory bytes we need to be careful
    # Newer versions support passing tuples: (filename, bytes, mime)
    
    # Note: explicit import check or error handling might be needed if dependencies vary
    
    conf = ConnectionConfig(
        MAIL_USERNAME=settings.mail_username,
        MAIL_PASSWORD=settings.mail_password,
        MAIL_FROM=settings.mail_from,
        MAIL_PORT=settings.mail_port,
        MAIL_SERVER=settings.mail_server,
        MAIL_STARTTLS=settings.mail_starttls,
        MAIL_SSL_TLS=settings.mail_ssl_tls,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True
    )

    recipient = email if email else current_user.username # Assuming username is email or valid
    # If username is not email, fallback to a placeholder or fail
    if "@" not in recipient:
        recipient = "admin@example.com" # Fallback for demo

    message = MessageSchema(
        subject=f"Fleet Analytics Report - {today}",
        recipients=[recipient],
        item_objects=[
            (f"Report_{today}.pdf", pdf_io.getvalue(), "application/pdf"),
            (f"Data_{today}.xlsx", xlsx_io.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        ],
        body=f"Please find attached the fleet analytics report for {today}.",
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    try:
        await fm.send_message(message)
        return {"message": f"Report sent to {recipient}"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )

