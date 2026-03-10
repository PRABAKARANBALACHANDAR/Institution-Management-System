from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth.dependencies import RequirePermission,get_current_user
from schemas.permissions import MYSQL_Permissions
from schemas.student import MYSQL_Students
from pydantic import BaseModel
from typing import List
from datetime import date
from crud.attendance_ops import (get_students_for_attendance,mark_batch_student_attendance,
                                  mark_faculty_attendance,get_student_attendance,get_faculty_attendance)

router=APIRouter()

class StudentAttRow(BaseModel):
    student_id:str
    is_present:bool

class BatchAttSubmit(BaseModel):
    date:date
    rows:List[StudentAttRow]

class FacultyAttCreate(BaseModel):
    faculty_id:str
    date:date
    is_present:bool

@router.get("/student/form")
def get_student_att_form(date:date=None,db:Session=Depends(get_db),
                         user=Depends(RequirePermission("post_stud_att"))):
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    att_date=date or __import__("datetime").date.today()
    return get_students_for_attendance(db,user.faculty_id,att_date)

@router.post("/student/batch")
def submit_batch_attendance(payload:BatchAttSubmit,db:Session=Depends(get_db),
                             user=Depends(RequirePermission("post_stud_att"))):
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    return mark_batch_student_attendance(db,user.faculty_id,payload.date,payload.rows)

@router.post("/faculty")
def mark_faculty_att(att:FacultyAttCreate,db:Session=Depends(get_db),
                     user=Depends(RequirePermission("post_faculty_att"))):
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    return mark_faculty_attendance(db,att.faculty_id,att.date,att.is_present)

@router.get("/student/{student_id}")
def get_student_att(
    student_id:str,
    db:Session=Depends(get_db),
    user:MYSQL_Permissions=Depends(get_current_user)
):
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    # Students can only see their own attendance
    if user.role=="student" and user.enrollment_id!=student_id:
        raise HTTPException(status_code=403,detail="Access denied")
    
    # Faculty can only see students assigned to them
    if user.role=="faculty":
        is_assigned = db.query(MYSQL_Students).filter(
            MYSQL_Students.id == student_id,
            MYSQL_Students.lecturer_id == user.faculty_id
        ).first()
        if not is_assigned:
            raise HTTPException(status_code=403, detail="You can only view attendance of students assigned to you")
    
    return get_student_attendance(db,student_id)

@router.get("/faculty/{faculty_id}")
def get_faculty_att(faculty_id:str,db:Session=Depends(get_db),
                    user=Depends(RequirePermission("get_faculty_att"))):
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    return get_faculty_attendance(db,faculty_id)

