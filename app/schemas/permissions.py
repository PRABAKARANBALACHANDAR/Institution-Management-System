from database import MYSQL_BASE, PG_BASE
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy import Enum as SqlEnum
from datetime import datetime
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict
from enum import Enum
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP

class Roles(str, Enum):
    ADMIN="admin"
    PRINCIPAL="principal"
    HOD="hod"
    FACULTY="faculty"
    STUDENT="student"

class MYSQL_Permissions(MYSQL_BASE):
    __tablename__ = "permissions"
    id=Column(String(50), primary_key=True)
    enrollment_id=Column(String(255), ForeignKey("students.id"),nullable=True)
    faculty_id=Column(String(255), ForeignKey("faculty.id"),nullable=True)
    username=Column(String(50), nullable=False, unique=True)
    password=Column(String(255), nullable=False)
    role=Column(SqlEnum(Roles), nullable=False)
    # create permissions
    post_principal=Column(Boolean, default=False)
    post_student=Column(Boolean, nullable=False)
    post_faculty=Column(Boolean, nullable=False)
    post_course=Column(Boolean, nullable=False)
    post_dept=Column(Boolean, nullable=False)
    post_marks=Column(Boolean, nullable=False)
    post_announcements=Column(Boolean, nullable=False)
    post_leave_req=Column(Boolean, nullable=False)
    post_queries=Column(Boolean, nullable=False)
    post_fees=Column(Boolean, nullable=False)
    post_faculty_att=Column(Boolean, nullable=False)
    post_stud_att=Column(Boolean, nullable=False)
    post_salary=Column(Boolean, nullable=False)
    # update permissions
    put_principal=Column(Boolean, nullable=False)
    put_student=Column(Boolean, nullable=False)
    put_faculty=Column(Boolean, nullable=False)
    put_course=Column(Boolean, nullable=False)
    put_dept=Column(Boolean, nullable=False)
    put_marks=Column(Boolean, nullable=False)
    put_announcements=Column(Boolean, nullable=False)
    put_leave_req=Column(Boolean, nullable=False)
    put_queries=Column(Boolean, nullable=False)
    put_salary=Column(Boolean, nullable=False)
    put_fees=Column(Boolean, nullable=False)
    # read permissions
    get_marks=Column(Boolean, nullable=False)
    get_student=Column(Boolean, nullable=False)
    get_faculty=Column(Boolean, nullable=False)
    get_announcements=Column(Boolean, nullable=False)
    get_dept=Column(Boolean, nullable=False)
    get_course=Column(Boolean, nullable=False)
    get_leave_req=Column(Boolean, nullable=False)
    get_queries=Column(Boolean, nullable=False)
    get_stud_att=Column(Boolean, nullable=False)
    get_faculty_att=Column(Boolean, nullable=False)
    get_salary=Column(Boolean, nullable=False)
    get_fees=Column(Boolean, nullable=False)
    get_analytics=Column(Boolean, nullable=False)
    # delete permissions
    delete_faculty=Column(Boolean, nullable=False)
    delete_student=Column(Boolean, nullable=False)
    delete_course=Column(Boolean, nullable=False)
    delete_dept=Column(Boolean, nullable=False)
    delete_announcements=Column(Boolean,nullable=False)
    created_at=Column(DateTime, default=datetime.now)
    updated_at=Column(DateTime, default=datetime.now, onupdate=datetime.now)
    enrollment=relationship("MYSQL_Students", back_populates="permissions")

class PermissionsResponse(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    enrollment_id: str | None
    faculty_id: str | None
    username: str
    role: str
    created_at: datetime
    updated_at: datetime