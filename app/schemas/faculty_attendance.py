from database import MYSQL_BASE,PG_BASE
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime,Date
from datetime import datetime
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import UUID,TIMESTAMP,REAL

class MYSQLFacultyAttendance(MYSQL_BASE):
    __tablename__="attendance"
    id=Column(String(20),primary_key=True)
    faculty_id=Column(String(20),ForeignKey("faculty.id"),nullable=False)
    date=Column(Date,nullable=False)
    is_present=Column(Boolean,nullable=False)
    created_at=Column(DateTime,default=datetime.now)
    updated_at=Column(DateTime,default=datetime.now,onupdate=datetime.now)
    faculty=relationship("MYSQL_Faculty",back_populates="attendance")

class PGFacultyAttendance(PG_BASE):
    __tablename__="dim_faculty_attendance"
    id=Column(UUID(as_uuid=True),primary_key=True)
    faculty_id=Column(UUID(as_uuid=True),ForeignKey("dim_faculty.id"),nullable=False)
    date=Column(Date,nullable=False)
    is_present=Column(Boolean,nullable=False)
    created_at=Column(TIMESTAMP,default=datetime.now)
    updated_at=Column(TIMESTAMP,default=datetime.now,onupdate=datetime.now)
