from database import PG_BASE
from sqlalchemy import Column, String, Integer, Boolean, REAL
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from datetime import datetime

class PG_FactRevenueReport(PG_BASE):
    __tablename__ = "dim_revenue_report"
    id = Column(UUID(as_uuid=True), primary_key=True)
    transaction_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    entity_name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False)
    amount = Column(REAL, nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    is_paid = Column(Boolean, nullable=False)
    paid_date = Column(TIMESTAMP, nullable=True)


class PG_FactTeacherPerformance(PG_BASE):
    __tablename__ = "dim_teacher_performance"
    id = Column(UUID(as_uuid=True), primary_key=True)
    faculty_id = Column(UUID(as_uuid=True), nullable=False)
    faculty_name = Column(String(100), nullable=False)
    total_classes = Column(Integer, nullable=False)
    attended_classes = Column(Integer, nullable=False)
    attendance_pct = Column(REAL, nullable=False)
    avg_student_score = Column(REAL, nullable=True)
    performance_score = Column(REAL, nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
