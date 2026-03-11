from datetime import datetime

from database import MYSQL_BASE
from sqlalchemy import JSON, Boolean, Column, Date, DateTime, Integer, String


class MYSQL_ETL_Watermark(MYSQL_BASE):
    __tablename__ = "etl_watermarks"

    entity_name = Column(String(50), primary_key=True)
    last_success_at = Column(DateTime, nullable=True)
    last_batch_id = Column(String(64), nullable=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


class MYSQL_Gold_Snapshot_Batch(MYSQL_BASE):
    __tablename__ = "gold_snapshot_batches"

    id = Column(String(64), primary_key=True)
    status = Column(String(20), nullable=False, default="snapshotted")
    source_counts = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    completed_at = Column(DateTime, nullable=True)


class MYSQL_Gold_Departments(MYSQL_BASE):
    __tablename__ = "gold_departments"

    source_id = Column(String(20), primary_key=True)
    name = Column(String(50), nullable=False)
    hod_id = Column(String(20), nullable=True)
    hod_name = Column(String(100), nullable=False)
    source_created_at = Column(DateTime, nullable=True)
    source_updated_at = Column(DateTime, nullable=True)
    extracted_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


class MYSQL_Gold_Snapshot_Departments(MYSQL_BASE):
    __tablename__ = "gold_snapshot_departments"

    batch_id = Column(String(64), primary_key=True)
    source_id = Column(String(20), primary_key=True)
    name = Column(String(50), nullable=False)
    hod_id = Column(String(20), nullable=True)
    hod_name = Column(String(100), nullable=False)
    source_created_at = Column(DateTime, nullable=True)
    source_updated_at = Column(DateTime, nullable=True)
    snapshot_at = Column(DateTime, default=datetime.now, nullable=False)


class MYSQL_Gold_Courses(MYSQL_BASE):
    __tablename__ = "gold_courses"

    source_id = Column(String(20), primary_key=True)
    name = Column(String(50), nullable=False)
    domain = Column(String(50), nullable=False)
    hod_id = Column(String(20), nullable=True)
    source_created_at = Column(DateTime, nullable=True)
    source_updated_at = Column(DateTime, nullable=True)
    extracted_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


class MYSQL_Gold_Snapshot_Courses(MYSQL_BASE):
    __tablename__ = "gold_snapshot_courses"

    batch_id = Column(String(64), primary_key=True)
    source_id = Column(String(20), primary_key=True)
    name = Column(String(50), nullable=False)
    domain = Column(String(50), nullable=False)
    hod_id = Column(String(20), nullable=True)
    source_created_at = Column(DateTime, nullable=True)
    source_updated_at = Column(DateTime, nullable=True)
    snapshot_at = Column(DateTime, default=datetime.now, nullable=False)


class MYSQL_Gold_Faculty(MYSQL_BASE):
    __tablename__ = "gold_faculty"

    source_id = Column(String(20), primary_key=True)
    name = Column(String(50), nullable=False)
    email = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=False)
    city = Column(String(50), nullable=False)
    is_lecturer = Column(Boolean, default=False)
    is_hod = Column(Boolean, default=False)
    is_principal = Column(Boolean, default=False)
    salary = Column(Integer, nullable=False)
    course_id = Column(String(20), nullable=True)
    department_id = Column(String(20), nullable=True)
    source_created_at = Column(DateTime, nullable=True)
    source_updated_at = Column(DateTime, nullable=True)
    extracted_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


class MYSQL_Gold_Snapshot_Faculty(MYSQL_BASE):
    __tablename__ = "gold_snapshot_faculty"

    batch_id = Column(String(64), primary_key=True)
    source_id = Column(String(20), primary_key=True)
    name = Column(String(50), nullable=False)
    email = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=False)
    city = Column(String(50), nullable=False)
    is_lecturer = Column(Boolean, default=False)
    is_hod = Column(Boolean, default=False)
    is_principal = Column(Boolean, default=False)
    salary = Column(Integer, nullable=False)
    course_id = Column(String(20), nullable=True)
    department_id = Column(String(20), nullable=True)
    source_created_at = Column(DateTime, nullable=True)
    source_updated_at = Column(DateTime, nullable=True)
    snapshot_at = Column(DateTime, default=datetime.now, nullable=False)


class MYSQL_Gold_Students(MYSQL_BASE):
    __tablename__ = "gold_students"

    source_id = Column(String(20), primary_key=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=True)
    email = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    city = Column(String(100), nullable=False)
    course_id = Column(String(20), nullable=True)
    lecturer_id = Column(String(20), nullable=True)
    year = Column(Integer, nullable=False)
    source_created_at = Column(DateTime, nullable=True)
    source_updated_at = Column(DateTime, nullable=True)
    extracted_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


class MYSQL_Gold_Snapshot_Students(MYSQL_BASE):
    __tablename__ = "gold_snapshot_students"

    batch_id = Column(String(64), primary_key=True)
    source_id = Column(String(20), primary_key=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=True)
    email = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    city = Column(String(100), nullable=False)
    course_id = Column(String(20), nullable=True)
    lecturer_id = Column(String(20), nullable=True)
    year = Column(Integer, nullable=False)
    source_created_at = Column(DateTime, nullable=True)
    source_updated_at = Column(DateTime, nullable=True)
    snapshot_at = Column(DateTime, default=datetime.now, nullable=False)


class MYSQL_Gold_StudentAttendance(MYSQL_BASE):
    __tablename__ = "gold_student_attendance"

    source_id = Column(String(20), primary_key=True)
    student_id = Column(String(20), nullable=False)
    date = Column(Date, nullable=False)
    is_present = Column(Boolean, nullable=False)
    marked_by = Column(String(20), nullable=True)
    source_created_at = Column(DateTime, nullable=True)
    source_updated_at = Column(DateTime, nullable=True)
    extracted_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


class MYSQL_Gold_Snapshot_StudentAttendance(MYSQL_BASE):
    __tablename__ = "gold_snapshot_student_attendance"

    batch_id = Column(String(64), primary_key=True)
    source_id = Column(String(20), primary_key=True)
    student_id = Column(String(20), nullable=False)
    date = Column(Date, nullable=False)
    is_present = Column(Boolean, nullable=False)
    marked_by = Column(String(20), nullable=True)
    source_created_at = Column(DateTime, nullable=True)
    source_updated_at = Column(DateTime, nullable=True)
    snapshot_at = Column(DateTime, default=datetime.now, nullable=False)


class MYSQL_Gold_FacultyAttendance(MYSQL_BASE):
    __tablename__ = "gold_faculty_attendance"

    source_id = Column(String(20), primary_key=True)
    faculty_id = Column(String(20), nullable=False)
    date = Column(Date, nullable=False)
    is_present = Column(Boolean, nullable=False)
    source_created_at = Column(DateTime, nullable=True)
    source_updated_at = Column(DateTime, nullable=True)
    extracted_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


class MYSQL_Gold_Snapshot_FacultyAttendance(MYSQL_BASE):
    __tablename__ = "gold_snapshot_faculty_attendance"

    batch_id = Column(String(64), primary_key=True)
    source_id = Column(String(20), primary_key=True)
    faculty_id = Column(String(20), nullable=False)
    date = Column(Date, nullable=False)
    is_present = Column(Boolean, nullable=False)
    source_created_at = Column(DateTime, nullable=True)
    source_updated_at = Column(DateTime, nullable=True)
    snapshot_at = Column(DateTime, default=datetime.now, nullable=False)


class MYSQL_Gold_StudentScores(MYSQL_BASE):
    __tablename__ = "gold_student_scores"

    source_id = Column(String(20), primary_key=True)
    semester = Column(Integer, nullable=False)
    student_id = Column(String(20), nullable=False)
    lecturer_id = Column(String(20), nullable=False)
    marks = Column(JSON, nullable=True)
    source_created_at = Column(DateTime, nullable=True)
    source_updated_at = Column(DateTime, nullable=True)
    extracted_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


class MYSQL_Gold_Snapshot_StudentScores(MYSQL_BASE):
    __tablename__ = "gold_snapshot_student_scores"

    batch_id = Column(String(64), primary_key=True)
    source_id = Column(String(20), primary_key=True)
    semester = Column(Integer, nullable=False)
    student_id = Column(String(20), nullable=False)
    lecturer_id = Column(String(20), nullable=False)
    marks = Column(JSON, nullable=True)
    source_created_at = Column(DateTime, nullable=True)
    source_updated_at = Column(DateTime, nullable=True)
    snapshot_at = Column(DateTime, default=datetime.now, nullable=False)


class MYSQL_Gold_Fees(MYSQL_BASE):
    __tablename__ = "gold_fees"

    source_id = Column(String(20), primary_key=True)
    student_id = Column(String(20), nullable=False)
    amount = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    is_paid = Column(Boolean, default=False)
    paid_date = Column(Date, nullable=True)
    source_created_at = Column(DateTime, nullable=True)
    source_updated_at = Column(DateTime, nullable=True)
    extracted_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


class MYSQL_Gold_Snapshot_Fees(MYSQL_BASE):
    __tablename__ = "gold_snapshot_fees"

    batch_id = Column(String(64), primary_key=True)
    source_id = Column(String(20), primary_key=True)
    student_id = Column(String(20), nullable=False)
    amount = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    is_paid = Column(Boolean, default=False)
    paid_date = Column(Date, nullable=True)
    source_created_at = Column(DateTime, nullable=True)
    source_updated_at = Column(DateTime, nullable=True)
    snapshot_at = Column(DateTime, default=datetime.now, nullable=False)


class MYSQL_Gold_Salary(MYSQL_BASE):
    __tablename__ = "gold_salary"

    source_id = Column(String(20), primary_key=True)
    faculty_id = Column(String(20), nullable=False)
    amount = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    is_paid = Column(Boolean, default=False)
    paid_date = Column(Date, nullable=True)
    source_created_at = Column(DateTime, nullable=True)
    source_updated_at = Column(DateTime, nullable=True)
    extracted_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


class MYSQL_Gold_Snapshot_Salary(MYSQL_BASE):
    __tablename__ = "gold_snapshot_salary"

    batch_id = Column(String(64), primary_key=True)
    source_id = Column(String(20), primary_key=True)
    faculty_id = Column(String(20), nullable=False)
    amount = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    is_paid = Column(Boolean, default=False)
    paid_date = Column(Date, nullable=True)
    source_created_at = Column(DateTime, nullable=True)
    source_updated_at = Column(DateTime, nullable=True)
    snapshot_at = Column(DateTime, default=datetime.now, nullable=False)
