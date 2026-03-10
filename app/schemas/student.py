from database import MYSQL_BASE,PG_BASE
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID,TIMESTAMP,REAL

class MYSQL_Students(MYSQL_BASE):
    __tablename__="students"
    id=Column(String(20),primary_key=True)
    name=Column(String(100),nullable=False)
    age=Column(Integer,nullable=False)
    email=Column(String(100),nullable=False,unique=True)
    phone=Column(String(20),nullable=False,unique=True)
    city=Column(String(100),nullable=False)
    course_id=Column(String(20),ForeignKey("courses.id"))
    lecturer_id=Column(String(20),ForeignKey("faculty.id"),nullable=True)
    year=Column(Integer,nullable=False)
    created_at=Column(DateTime,default=datetime.now)
    updated_at=Column(DateTime,default=datetime.now,onupdate=datetime.now)
    course=relationship("MYSQL_Courses",back_populates="students")
    lecturer=relationship("MYSQL_Faculty",back_populates="assigned_students")
    attendance=relationship("MYSQLStudentAttendance",back_populates="student")
    fees=relationship("MYSQL_Fees", back_populates="student")
    scores=relationship("MYSQLStudentScores", back_populates="student")
    leave_requests=relationship("MYSQL_Leave_Req", primaryjoin="and_(MYSQL_Leave_Req.role=='student', foreign(MYSQL_Leave_Req.role_id)==MYSQL_Students.id)")
    permissions=relationship("MYSQL_Permissions", back_populates="enrollment")
    

class PG_Students(PG_BASE):
    __tablename__="dim_student"
    id=Column(UUID(as_uuid=True),primary_key=True)
    name=Column(String(100),nullable=False)
    age=Column(Integer,nullable=True)
    email=Column(String(100),nullable=False,unique=True)
    phone=Column(String(20),nullable=False,unique=True)
    city=Column(String(100),nullable=False)
    course_id=Column(UUID(as_uuid=True),ForeignKey("dim_course.id"))
    lecturer_id=Column(UUID(as_uuid=True),ForeignKey("dim_faculty.id"),nullable=True)
    year=Column(Integer,nullable=False)
    created_at=Column(TIMESTAMP,default=datetime.now)
