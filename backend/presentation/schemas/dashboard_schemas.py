from datetime import datetime

from pydantic import BaseModel
from typing import List, Optional

class DashboardSummary(BaseModel):
    critical_count: int
    monitor_count: int
    stable_count: int
    average_risk_percent: int

class EmployeeDashboardItem(BaseModel):
    id: int
    name: str
    role: str
    department: str
    risk_score: int
    status: str
    trend: str
    has_feedback: bool
    hire_date: Optional[datetime]

class DashboardResponse(BaseModel):
    summary: DashboardSummary
    employees: List[EmployeeDashboardItem]
    total: int
    page: int
    page_size: int
    total_pages: int
