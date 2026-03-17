from database import MYSQL_BASE,PG_BASE
from sqlalchemy import Column,String,Integer,Boolean,ForeignKey,DateTime,Date
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID,REAL,TIMESTAMP

class MYSQL_Salary(MYSQL_BASE):
    __tablename__="salary"
    id=Column(String(20),primary_key=True)
    faculty_id=Column(String(20),ForeignKey("faculty.id"),nullable=False)
    amount=Column(Integer,nullable=False)
    month=Column(Integer,nullable=False)
    year=Column(Integer,nullable=False)
    is_paid=Column(Boolean,default=False)
    paid_date=Column(Date,nullable=True)
    created_at=Column(DateTime,default=datetime.now)
    updated_at=Column(DateTime,default=datetime.now,onupdate=datetime.now)
    faculty=relationship("MYSQL_Faculty",back_populates="salary_details")
    
class PG_Salary(PG_BASE):
    __tablename__="dim_salary"
    id=Column(UUID(as_uuid=True),primary_key=True)
    faculty_id=Column(UUID(as_uuid=True),ForeignKey("fact_faculty.id"),nullable=False)
    amount=Column(REAL,nullable=False)
    month=Column(Integer,nullable=False)
    year=Column(Integer,nullable=False)
    is_paid=Column(Boolean,default=False)
    paid_date=Column(TIMESTAMP,nullable=True)
