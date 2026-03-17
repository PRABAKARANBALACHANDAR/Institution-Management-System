from database import MYSQL_BASE,PG_BASE
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime
from datetime import datetime
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import UUID,TIMESTAMP,REAL

class MYSQL_Departments(MYSQL_BASE):
    __tablename__="departments"
    id=Column(String(20),primary_key=True)
    name=Column(String(50),nullable=False)
    hod_id=Column(String(20),ForeignKey("faculty.id",use_alter=True,name="fk_departments_hod"),nullable=True)
    hod_name=Column(String(50),nullable=False)
    faculty=relationship("MYSQL_Faculty",back_populates="department",foreign_keys="[MYSQL_Faculty.department_id]")
    hod=relationship("MYSQL_Faculty",foreign_keys=[hod_id])
    created_at=Column(DateTime,default=datetime.now)
    updated_at=Column(DateTime,default=datetime.now,onupdate=datetime.now)


class PG_Departments(PG_BASE):
    __tablename__="dim_department"
    id=Column(UUID(as_uuid=True),primary_key=True)
    name=Column(String(50),nullable=False)
    hod_id=Column(UUID(as_uuid=True),ForeignKey("fact_faculty.id"))
    hod_name=Column(String(100),nullable=False)
