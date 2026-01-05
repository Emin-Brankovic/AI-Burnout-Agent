"""
Database Seeder for Employee Burnout System

Seeds the database with:
- Departments
- 100 Employees (from CSV data)
- Daily logs (18,000 records from CSV)
"""

import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from faker import Faker
import random
import os

from backend.infrastructure.persistence.database import SessionLocal, Employee, Department, DailyLog
from backend.domain.enums.enums import DailyLogStatus

fake = Faker()


def seed_departments(db: Session):
    """Seed departments."""
    print("   📁 Seeding departments...")

    departments_data = [
        {"name": "Engineering", "description": "Software development and technical innovation"},
        {"name": "Product Management", "description": "Product strategy and roadmap planning"},
        {"name": "Design", "description": "UI/UX and product design"},
        {"name": "Marketing", "description": "Marketing and brand management"},
        {"name": "Sales", "description": "Sales and business development"},
        {"name": "Customer Success", "description": "Customer support and success"},
        {"name": "Human Resources", "description": "HR and people operations"},
        {"name": "Finance", "description": "Finance and accounting"},
        {"name": "Operations", "description": "Operations and logistics"},
        {"name": "Data Science", "description": "Data analysis and machine learning"}
    ]

    departments = []
    for dept_data in departments_data:
        dept = Department(
            name=dept_data["name"],
            description=dept_data["description"]
        )
        db.add(dept)
        departments.append(dept)

    db.commit()
    print(f"   ✅ Created {len(departments)} departments")
    return departments


def seed_employees(db: Session, departments: list, num_employees: int = 100):
    """Seed employees based on CSV Employee_IDs."""
    print(f"   👥 Seeding {num_employees} employees...")

    # Job titles by department
    job_titles = {
        "Engineering": ["Software Engineer", "Senior Engineer", "Tech Lead", "Engineering Manager"],
        "Product Management": ["Product Manager", "Senior PM", "Product Owner", "VP of Product"],
        "Design": ["UX Designer", "UI Designer", "Design Lead", "Creative Director"],
        "Marketing": ["Marketing Manager", "Content Specialist", "Marketing Director", "Brand Manager"],
        "Sales": ["Account Executive", "Sales Manager", "Business Development", "Sales Director"],
        "Customer Success": ["Customer Success Manager", "Support Specialist", "CS Lead"],
        "Human Resources": ["HR Manager", "Recruiter", "People Operations", "HR Director"],
        "Finance": ["Financial Analyst", "Accountant", "Finance Manager", "CFO"],
        "Operations": ["Operations Manager", "Logistics Coordinator", "Operations Director"],
        "Data Science": ["Data Scientist", "ML Engineer", "Data Analyst", "Analytics Lead"]
    }

    employees = []
    for employee_id in range(1, num_employees + 1):
        # Assign to random department
        department = random.choice(departments)

        # Get appropriate job title
        title = random.choice(job_titles[department.name])

        # Generate employee data
        first_name = fake.first_name()
        last_name = fake.last_name()

        employee = Employee(
            id=employee_id,  # Use same ID as CSV
            first_name=first_name,
            last_name=last_name,
            email=f"{first_name.lower()}.{last_name.lower()}@company.com",
            phone=fake.phone_number(),
            department_id=department.id,
            job_title=title,
            hire_date=fake.date_between(start_date='-5y', end_date='-1y'),
            salary=random.randint(1000, 7000),
            high_burnout_streak=0,
            last_alert_sent=None
        )

        db.add(employee)
        employees.append(employee)

    db.commit()
    print(f"   ✅ Created {len(employees)} employees")
    return employees


def seed_daily_logs_from_csv(db: Session, csv_path: str = 'backend/data/employee_burnout_form_data_final.csv'):
    """Seed daily logs from CSV file."""
    print(f"   📊 Seeding daily logs from CSV...")

    # Check if CSV exists
    if not os.path.exists(csv_path):
        print(f"   ⚠️ CSV file not found at {csv_path}")
        return

    # Read CSV
    df = pd.read_csv(csv_path)
    print(f"      Found {len(df)} records in CSV")
    print(f"      Employees: {df['Employee_ID'].nunique()}")

    # Start date (180 days ago from today)
    start_date = datetime.now() - timedelta(days=180)

    # Group by employee to assign sequential dates
    employee_logs = {}
    for employee_id in df['Employee_ID'].unique():
        employee_logs[employee_id] = df[df['Employee_ID'] == employee_id].to_dict('records')

    total_logs = 0
    for employee_id, logs in employee_logs.items():
        current_date = start_date

        for log_data in logs:
            # Create daily log
            daily_log = DailyLog(
                employee_id=log_data['Employee_ID'],
                log_date=current_date,
                hours_worked=log_data['Work_Hours_Per_Day'],
                hours_slept=log_data['Sleep_Hours_Per_Night'],
                daily_personal_time=log_data['Personal_Time_Hours_Per_Day'],
                motivation_level=log_data['Motivation_Level'],
                stress_level=log_data['Work_Stress_Level'],
                workload_intensity=log_data['Workload_Intensity'],
                overtime_hours_today=log_data['Overtime_Hours_Today'],
                status=DailyLogStatus.ANALYZED,  # Mark as analyzed since we have burnout data
                processed_at=current_date
            )

            db.add(daily_log)
            total_logs += 1
            current_date += timedelta(days=1)

        # Commit in batches every 10 employees
        if employee_id % 10 == 0:
            db.commit()

    db.commit()
    print(f"   ✅ Created {total_logs} daily logs")


def run_seeder():
    """
    Main seeder function - called from main.py on startup.
    Only seeds if database is empty.
    """
    print("\n🌱 Seeding database with initial data...")

    db = SessionLocal()

    try:
        # Seed departments
        departments = seed_departments(db)

        # Seed employees (100 from CSV)
        employees = seed_employees(db, departments, num_employees=100)

        # Seed daily logs from CSV
        seed_daily_logs_from_csv(db)

        print("\n✅ Database seeding completed successfully!")
        print(f"   - Departments: {len(departments)}")
        print(f"   - Employees: {len(employees)}")
        print(f"   - Daily Logs: ~18,000 (180 days × 100 employees)")

    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


# # For standalone execution
# if __name__ == "__main__":
#     print("=" * 80)
#     print("🌱 STANDALONE DATABASE SEEDER")
#     print("=" * 80)
#
#     # Initialize database first
#     from backend.infrastructure.persistence.database import init_db
#     init_db()
#
#     # Run seeder
#     run_seeder()
#
#     print("=" * 80)