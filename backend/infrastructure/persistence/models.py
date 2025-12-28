from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from datetime import datetime
from typing import List, Optional


class Base(DeclarativeBase):
    pass


class Department(Base):
    __tablename__ = 'departments'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    employees: Mapped[List["Employee"]] = relationship(back_populates="department")


class Employee(Base):
    __tablename__ = 'employees'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    department_id: Mapped[Optional[int]] = mapped_column(ForeignKey('departments.id'))
    hire_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    department: Mapped[Optional["Department"]] = relationship(back_populates="employees")
    daily_logs: Mapped[List["DailyLog"]] = relationship(back_populates="employee")


class DailyLog(Base):
    __tablename__ = 'daily_logs'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey('employees.id'), nullable=False)
    log_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    hours_worked: Mapped[Optional[float]] = mapped_column(nullable=False)
    hours_slept: Mapped[Optional[float]] = mapped_column(nullable=False)
    daily_personal_time: Mapped[Optional[float]] = mapped_column(nullable=False)
    motivation_level: Mapped[Optional[int]] = mapped_column(nullable=False)
    stress_level: Mapped[Optional[int]] = mapped_column(nullable=False)
    workload_intensity: Mapped[Optional[int]] = mapped_column(nullable=False)
    overtime_hours_today: Mapped[Optional[float]] = mapped_column(nullable=False)

    employee: Mapped["Employee"] = relationship(back_populates="daily_logs")
    agent_predictions: Mapped[List["AgentPrediction"]] = relationship(back_populates="daily_log")


class AgentPrediction(Base):
    __tablename__ = 'agent_predictions'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    daily_log_id: Mapped[int] = mapped_column(ForeignKey('daily_logs.id'), nullable=False)
    prediction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    prediction_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    daily_log: Mapped["DailyLog"] = relationship(back_populates="agent_predictions")