from database import MYSQL_BASE,PG_BASE
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime,Date
from datetime import datetime
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import UUID,TIMESTAMP,REAL

class MYSQLStudentAttendance(MYSQL_BASE):
    __tablename__="student_attendance"
    id=Column(String(20),primary_key=True)
    student_id = Column(String(20), ForeignKey('students.id'), nullable=False)
    date=Column(Date,nullable=False)
    is_present=Column(Boolean,nullable=False)
    marked_by=Column(String(20),ForeignKey("faculty.id"),nullable=True)
    created_at=Column(DateTime,default=datetime.now)
    updated_at=Column(DateTime,default=datetime.now,onupdate=datetime.now)
    student=relationship("MYSQL_Students",back_populates="attendance")
    marked_by_faculty=relationship("MYSQL_Faculty",foreign_keys="[MYSQLStudentAttendance.marked_by]")

class PGStudentAttendance(PG_BASE):
    __tablename__="fact_student_attendance"
    id=Column(UUID(as_uuid=True),primary_key=True)
    student_id=Column(UUID(as_uuid=True),ForeignKey("fact_student.id"),nullable=False)
    date=Column(Date,nullable=False)
    is_present=Column(Boolean,nullable=False)
