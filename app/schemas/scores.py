from database import MYSQL_BASE,PG_BASE
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime,JSON
from datetime import datetime
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import UUID,TIMESTAMP,REAL

class MYSQLStudentScores(MYSQL_BASE):
    __tablename__ = "student_scores"
    id=Column(String(20),primary_key=True)
    semester=Column(Integer,nullable=False)
    student_id=Column(String(20),ForeignKey("students.id"),nullable=False)
    lecturer_id=Column(String(20),ForeignKey("faculty.id"),nullable=False)
    marks=Column(JSON)
    created_at=Column(DateTime,default=datetime.now)
    updated_at=Column(DateTime,default=datetime.now,onupdate=datetime.now)
    student=relationship("MYSQL_Students",back_populates="scores")
    lecturer=relationship("MYSQL_Faculty",foreign_keys=[lecturer_id])

class PGStudentScores(PG_BASE):
    __tablename__="fact_student_scores"
    id=Column(UUID(as_uuid=True),primary_key=True)
    semester=Column(Integer,nullable=False)
    student_id=Column(UUID(as_uuid=True),ForeignKey("dim_student.id"),nullable=False)
    lecturer_id=Column(UUID(as_uuid=True),ForeignKey("dim_faculty.id"),nullable=False)
    avg_marks=Column(REAL,nullable=True)