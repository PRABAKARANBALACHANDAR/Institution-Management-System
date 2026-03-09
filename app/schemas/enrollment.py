from database import MYSQL_BASE,PG_BASE
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Date
from datetime import datetime
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import UUID,TIMESTAMP,REAL,TIMESTAMP

class MYSQL_StudentEnrollment(MYSQL_BASE):
    __tablename__="enrollment"
    id=Column(String(20),primary_key=True)
    student_id=Column(String(20),ForeignKey("students.id"),nullable=False)
    course_id=Column(String(20),ForeignKey("courses.id"),nullable=False)
    enrollment_date=Column(Date,nullable=False)
    student=relationship("MYSQL_Students",back_populates="enrollments")
    course=relationship("MYSQL_Courses",back_populates="enrollments")
    permissions=relationship("MYSQL_Permissions",back_populates="enrollment")
    created_at=Column(DateTime,default=datetime.now)
    updated_at=Column(DateTime,default=datetime.now,onupdate=datetime.now)

class MYSQL_FacultyAssignment(MYSQL_BASE):
    __tablename__="assignment_faculty"
    id=Column(String(20),primary_key=True)
    faculty_id=Column(String(20),ForeignKey("faculty.id"),nullable=False)
    course_id=Column(String(20),ForeignKey("courses.id"),nullable=False)
    department_id=Column(String(20),ForeignKey("departments.id"),nullable=True)
    assignment_date=Column(Date,nullable=False)
    faculty=relationship("MYSQL_Faculty",back_populates="assignments")
    course=relationship("MYSQL_Courses",back_populates="assignments")
    department=relationship("MYSQL_Departments",back_populates="assignments")
    created_at=Column(DateTime,default=datetime.now)
    updated_at=Column(DateTime,default=datetime.now,onupdate=datetime.now)

class MYSQL_LecturerStudentAssignment(MYSQL_BASE):
    __tablename__="assignment_lecturer_student"
    id=Column(String(20),primary_key=True)
    student_id=Column(String(20),ForeignKey("students.id"),nullable=False)
    lecturer_id=Column(String(20),ForeignKey("faculty.id"),nullable=False)
    course_id=Column(String(20),ForeignKey("courses.id"),nullable=False)
    created_at=Column(DateTime,default=datetime.now)
    updated_at=Column(DateTime,default=datetime.now,onupdate=datetime.now)

class PG_FactStudentEnrollment(PG_BASE):
    __tablename__="fact_student_enrollment"
    id=Column(UUID(as_uuid=True),primary_key=True)
    student_id=Column(UUID(as_uuid=True),ForeignKey("dim_student.id"),nullable=False)
    course_id=Column(UUID(as_uuid=True),ForeignKey("dim_course.id"),nullable=False)
    enrollment_date=Column(TIMESTAMP,nullable=False)

class PG_FactFacultyAssignment(PG_BASE):
    __tablename__="fact_faculty_assignment"
    id=Column(UUID(as_uuid=True),primary_key=True)
    faculty_id=Column(UUID(as_uuid=True),ForeignKey("dim_faculty.id"),nullable=False)
    course_id=Column(UUID(as_uuid=True),ForeignKey("dim_course.id"),nullable=False)
    department_id=Column(UUID(as_uuid=True),ForeignKey("dim_department.id"),nullable=True)
    assignment_date=Column(TIMESTAMP,nullable=False)