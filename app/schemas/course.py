from database import MYSQL_BASE, PG_BASE
from sqlalchemy import Column, String, ForeignKey, DateTime
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID,TIMESTAMP

class MYSQL_Courses(MYSQL_BASE):
    __tablename__="courses"
    id=Column(String(20), primary_key=True)
    name=Column(String(50), nullable=False)
    domain=Column(String(50), nullable=False)
    hod_id=Column(String(20), ForeignKey("faculty.id"),nullable=True)
    faculty=relationship("MYSQL_Faculty",back_populates="course",foreign_keys="[MYSQL_Faculty.course_id]")
    hod=relationship("MYSQL_Faculty",foreign_keys=[hod_id])
    students=relationship("MYSQL_Students",back_populates="course")
    created_at=Column(DateTime, default=datetime.now)
    updated_at=Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
class PG_Courses(PG_BASE):
    __tablename__="dim_course"
    id=Column(UUID(as_uuid=True), primary_key=True)
    name=Column(String(50), nullable=False)
    domain=Column(String(50), nullable=False)
    hod_id=Column(UUID(as_uuid=True), ForeignKey("fact_faculty.id"),nullable=True)
