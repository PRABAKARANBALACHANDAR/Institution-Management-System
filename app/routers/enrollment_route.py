from datetime import date
from typing import Optional, List

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth.dependencies import RequirePermission
from crud.faculty_ops import create_faculty_db
from crud.student_ops import create_student_db
from crud.utils import generate_custom_id
from database import get_db
from schemas.enrollment import (
    MYSQL_FacultyAssignment,
    MYSQL_LecturerStudentAssignment,
    MYSQL_StudentEnrollment,
)

router = APIRouter(prefix="/enrollment", tags=["Enrollment"])


class StudentCoreCreate(BaseModel):
    name: str
    age: int
    email: str
    phone: str
    city: str
    course_id: str
    year: int


class StudentAssignmentInput(BaseModel):
    course_id: Optional[str] = None
    enrollment_date: Optional[date] = None
    lecturer_id: Optional[str] = None


class EnrollStudentFullRequest(BaseModel):
    student: StudentCoreCreate
    assignment: StudentAssignmentInput = Field(default_factory=StudentAssignmentInput)


class FacultyCoreCreate(BaseModel):
    name: str
    email: str
    phone: str
    city: str
    is_lecturer: bool = False
    is_hod: bool = False
    is_principal: bool = False
    salary: int
    department_id: Optional[str] = None
    course_id: Optional[str] = None


class FacultyAssignmentInput(BaseModel):
    course_id: str
    assignment_date: Optional[date] = None
    department_id: Optional[str] = None
    assign_students: List[str] = Field(default_factory=list)


class EnrollFacultyFullRequest(BaseModel):
    faculty: FacultyCoreCreate
    assignment: FacultyAssignmentInput


@router.post("/student/full")
def enroll_student_full(
    payload: EnrollStudentFullRequest,
    db: Session = Depends(get_db),
    user=Depends(RequirePermission("post_student")),
):
    try:
        # Create student without permissions (auto-generated based on role)
        student = create_student_db(
            db,
            payload.student.model_dump(),
            auto_commit=False,
        )

        enrollment_course_id = payload.assignment.course_id or student.course_id
        enrollment_record = MYSQL_StudentEnrollment(
            id=generate_custom_id(db, MYSQL_StudentEnrollment, "E"),
            student_id=student.id,
            course_id=enrollment_course_id,
            enrollment_date=payload.assignment.enrollment_date or date.today(),
        )
        db.add(enrollment_record)

        lecturer_assignment_id = None
        if payload.assignment.lecturer_id:
            lecturer_assignment = MYSQL_LecturerStudentAssignment(
                id=generate_custom_id(db, MYSQL_LecturerStudentAssignment, "LS"),
                student_id=student.id,
                lecturer_id=payload.assignment.lecturer_id,
                course_id=enrollment_course_id,
            )
            db.add(lecturer_assignment)
            lecturer_assignment_id = lecturer_assignment.id

        db.commit()
        return {
            "message": "Student enrolled successfully",
            "student_id": student.id,
            "enrollment_id": enrollment_record.id,
            "lecturer_assignment_id": lecturer_assignment_id,
        }
    except Exception:
        db.rollback()
        raise


@router.post("/faculty/full")
def enroll_faculty_full(
    payload: EnrollFacultyFullRequest,
    db: Session = Depends(get_db),
    user=Depends(RequirePermission("post_faculty")),
):
    try:
        # Create faculty without permissions (auto-generated based on role)
        faculty = create_faculty_db(
            db,
            payload.faculty.model_dump(),
            auto_commit=False,
        )

        assignment_record = MYSQL_FacultyAssignment(
            id=generate_custom_id(db, MYSQL_FacultyAssignment, "FA"),
            faculty_id=faculty.id,
            course_id=payload.assignment.course_id,
            department_id=payload.assignment.department_id,
            assignment_date=payload.assignment.assignment_date or date.today(),
        )
        db.add(assignment_record)

        lecturer_assignment_ids = []
        for student_id in payload.assignment.assign_students:
            rec = MYSQL_LecturerStudentAssignment(
                id=generate_custom_id(db, MYSQL_LecturerStudentAssignment, "LS"),
                student_id=student_id,
                lecturer_id=faculty.id,
                course_id=payload.assignment.course_id,
            )
            db.add(rec)
            lecturer_assignment_ids.append(rec.id)

        db.commit()
        return {
            "message": "Faculty enrolled successfully",
            "faculty_id": faculty.id,
            "faculty_assignment_id": assignment_record.id,
            "lecturer_student_assignment_ids": lecturer_assignment_ids,
        }
    except Exception:
        db.rollback()
        raise

