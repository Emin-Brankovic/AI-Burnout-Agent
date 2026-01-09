from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from backend.infrastructure.persistence.database import Employee, DailyLog, AgentPrediction, Department
from backend.domain.enums.enums import BurnoutRiskLevel

class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_dashboard_data(
        self, 
        page: int = 1, 
        page_size: int = 10,
        department: str | None = None,
        status: str | None = None,
        trend: str | None = None
    ) -> Dict[str, Any]:
        # 1. Build base query for employees
        base_query = self.db.query(Employee)
        
        # Apply department filter if provided
        if department:
            base_query = base_query.join(Department).filter(Department.name == department)
        
        all_employees = base_query.all()
        
        # 2. Build employee data with predictions and apply filters
        employee_data_list = []
        
        for emp in all_employees:
            # Get latest prediction for this employee
            latest_prediction = (
                self.db.query(AgentPrediction)
                .join(DailyLog)
                .filter(DailyLog.employee_id == emp.id)
                .order_by(desc(AgentPrediction.created_at))
                .first()
            )
            
            # Get second latest prediction for trend
            prev_prediction = (
                self.db.query(AgentPrediction)
                .join(DailyLog)
                .filter(DailyLog.employee_id == emp.id)
                .order_by(desc(AgentPrediction.created_at))
                .offset(1)
                .first()
            )

            risk_score = 0
            emp_status = "NORMAL"
            emp_trend = "stable"
            has_feedback = False

            if latest_prediction:
                try:
                    risk_value = float(latest_prediction.burnout_rate) if latest_prediction.burnout_rate else 0.0
                except (ValueError, TypeError):
                    risk_value = 0.0
                
                risk_score = int(risk_value * 100)
                emp_status = latest_prediction.burnout_risk
                has_feedback = latest_prediction.human_validation is not None
                
                # Calculate trend
                if prev_prediction:
                    try:
                        prev_risk_value = float(prev_prediction.burnout_rate) if prev_prediction.burnout_rate else 0.0
                    except (ValueError, TypeError):
                        prev_risk_value = 0.0
                    
                    if risk_value > prev_risk_value + 0.05:
                        emp_trend = "increasing"
                    elif risk_value < prev_risk_value - 0.05:
                        emp_trend = "decreasing"

            department_name = emp.department.name if emp.department else "Unknown"
            
            employee_data_list.append({
                "employee": emp,
                "id": emp.id,
                "name": f"{emp.first_name} {emp.last_name}",
                "role": emp.job_title or "Employee",
                "department": department_name,
                "risk_score": risk_score,
                "status": emp_status,
                "trend": emp_trend,
                "has_feedback": has_feedback
            })
        
        # 3. Apply status and trend filters
        filtered_employees = employee_data_list
        
        if status:
            filtered_employees = [e for e in filtered_employees if e["status"].upper() == status.upper()]
        
        if trend:
            filtered_employees = [e for e in filtered_employees if e["trend"].lower() == trend.lower()]
        
        # 4. Calculate summary statistics from filtered data
        critical_count = 0
        monitor_count = 0
        stable_count = 0
        total_risk_sum = 0
        prediction_count = 0
        
        for emp_data in filtered_employees:
            emp_status = emp_data["status"]
            risk_score = emp_data["risk_score"]
            
            if emp_status.lower() == BurnoutRiskLevel.CRITICAL:
                critical_count += 1
            elif emp_status.lower() in [BurnoutRiskLevel.HIGH, BurnoutRiskLevel.MEDIUM]:
                monitor_count += 1
            else:
                stable_count += 1
            
            if risk_score > 0:
                total_risk_sum += risk_score
                prediction_count += 1
        
        average_risk = int(total_risk_sum / prediction_count) if prediction_count > 0 else 0
        
        # 5. Paginate filtered employees
        total_count = len(filtered_employees)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_employees = filtered_employees[start_idx:end_idx]
        
        # 6. Build response items (remove employee object)
        employee_items = []
        for emp_data in paginated_employees:
            employee_items.append({
                "id": emp_data["id"],
                "name": emp_data["name"],
                "role": emp_data["role"],
                "department": emp_data["department"],
                "risk_score": emp_data["risk_score"],
                "status": emp_data["status"],
                "trend": emp_data["trend"],
                "has_feedback": emp_data["has_feedback"],
                "hire_date": emp_data["employee"].hire_date
            })

        import math
        total_pages = math.ceil(total_count / page_size) if page_size > 0 else 0

        return {
            "summary": {
                "critical_count": critical_count,
                "monitor_count": monitor_count,
                "stable_count": stable_count,
                "average_risk_percent": average_risk
            },
            "employees": employee_items,
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
