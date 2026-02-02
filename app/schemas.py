"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import date, datetime


class UserCreate(BaseModel):
    """Schema for creating a new user"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str | None = Field(None, pattern=r'^\S+@\S+\.\S+$')
    password: str = Field(..., min_length=6)
    role: str = "user"


class UserPasswordChange(BaseModel):
    """Schema for changing password"""
    current_password: str
    new_password: str = Field(..., min_length=6)


class UserOut(BaseModel):
    """Schema for user response"""
    id: int
    username: str
    email: str | None = None
    role: str
    account_id: str | None = None
    last_login: datetime | None = None
    is_locked: bool = False
    
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str


class PasswordResetRequest(BaseModel):
    email: str = Field(..., pattern=r'^\S+@\S+\.\S+$')


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)


class FleetRecordBase(BaseModel):
    """Base schema for fleet record"""
    date: date
    fleet: str = Field(..., min_length=1)
    amount: float = Field(..., ge=0)


class FleetRecordOut(FleetRecordBase):
    """Schema for fleet record response"""
    id: int

    model_config = ConfigDict(from_attributes=True)


class FleetSummary(BaseModel):
    """Schema for fleet summary items"""
    fleet: str
    total_amount: float
    record_count: int
    remittance: float = 0.0


class DailySubtotal(BaseModel):
    """Schema for daily fleet performance"""
    date: date
    fleet: str
    daily_total: float
    pax: int


class DashboardStats(BaseModel):
    """Schema for KPI cards"""
    total_revenue: float
    total_records: int
    top_performing_fleet: str
    average_trip_revenue: float
    predicted_revenue: float | None = 0.0
    revenue_trend_percent: float | None = 0.0 # Percentage change WoW


class FilterOptions(BaseModel):
    """Schema for available filter options"""
    fleets: list[str]
    min_date: date | None
    max_date: date | None


class Anomaly(BaseModel):
    """Schema for data anomalies"""
    date: date
    fleet: str
    amount: float
    reason: str
    severity: str # "high", "medium", "low"

class AnalyticsResponse(BaseModel):
    """Comprehensive analytics response"""
    records: list[FleetRecordOut]
    fleet_summaries: list[FleetSummary]
    daily_subtotals: list[DailySubtotal]
    dashboard_stats: DashboardStats
    anomalies: list[Anomaly] = []

class ChartDataPoint(BaseModel):
    label: str
    value: float


class ChartResponse(BaseModel):
    revenue_trend: list[ChartDataPoint]
    revenue_by_fleet: list[ChartDataPoint]
    top_fleets: list[ChartDataPoint]
    anomalies: list[Anomaly] = []


class AuditLogOut(BaseModel):
    """Schema for audit log response"""
    id: int
    user_id: int | None
    username: str | None
    action: str
    details: str | None
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """Schema for updating user role/details"""
    username: str | None = Field(None, min_length=3, max_length=50)
    email: str | None = Field(None, pattern=r'^\S+@\S+\.\S+$')
    role: str | None = None
    account_id: str | None = None


class SystemSettingBase(BaseModel):
    key: str
    value: str
    description: str | None = None

class SystemSettingOut(SystemSettingBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
class NotificationOut(BaseModel):
    """Schema for notification response"""
    id: int
    user_id: int | None
    title: str
    message: str
    type: str
    is_read: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
