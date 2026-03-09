from database import MYSQL_BASE,PG_BASE
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID,TIMESTAMP,REAL

class MYSQL_Faculty(MYSQL_BASE):
    __tablename__="faculty"
    id=Column(String(20),primary_key=True)
    name=Column(String(50),nullable=False)
    email=Column(String(50),nullable=False,unique=True)
    phone=Column(String(20),nullable=False,unique=True)
    city=Column(String(50),nullable=False)
    is_lecturer=Column(Boolean,default=False)
    is_hod=Column(Boolean,default=False)
    is_principal=Column(Boolean,default=False)
    salary=Column(Integer,nullable=False)
    course_id=Column(String(20),ForeignKey("courses.id"),nullable=True)
    department_id=Column(String(20),ForeignKey("departments.id"),nullable=True)
    department=relationship("MYSQL_Departments",foreign_keys=[department_id],back_populates="faculty")
    course=relationship("MYSQL_Courses",foreign_keys=[course_id],back_populates="faculty")
    assignments=relationship("MYSQL_FacultyAssignment",back_populates="faculty")
    assigned_students=relationship("MYSQL_Students",foreign_keys="[MYSQL_Students.lecturer_id]",back_populates="lecturer")
    attendance=relationship("MYSQLFacultyAttendance",back_populates="faculty")
    salary_details=relationship("MYSQL_Salary",back_populates="faculty")
    leave_requests=relationship("MYSQL_Leave_Req",primaryjoin="and_(MYSQL_Leave_Req.role=='faculty', foreign(MYSQL_Leave_Req.role_id)==MYSQL_Faculty.id)", overlaps="leave_requests")
    created_at=Column(DateTime,default=datetime.now)
    updated_at=Column(DateTime,default=datetime.now,onupdate=datetime.now)    

class PG_Faculty(PG_BASE):
    __tablename__="dim_faculty"
    id=Column(UUID(as_uuid=True),primary_key=True)
    name=Column(String(50),nullable=False)
    email=Column(String(50),nullable=False,unique=True)
    phone=Column(String(20),nullable=False,unique=True)
    city=Column(String(50),nullable=False)
    is_lecturer=Column(Boolean,default=False)
    is_hod=Column(Boolean,default=False)
    is_principal=Column(Boolean,default=False,unique=True)
    salary=Column(REAL,nullable=False)
    course_id=Column(UUID(as_uuid=True),ForeignKey("dim_course.id"),nullable=True)
    department_id=Column(UUID(as_uuid=True),ForeignKey("dim_department.id"),nullable=True)
    created_at=Column(TIMESTAMP,default=datetime.now)
    updated_at=Column(TIMESTAMP,default=datetime.now,onupdate=datetime.now)    