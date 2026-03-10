from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from database import get_db
from auth.dependencies import RequirePermission, get_current_user
from crud.student_ops import create_student_db, get_all_students_db, get_student_db, update_student_db, delete_student_db
from crud.permissions_ops import create_permissions
from schemas.permissions import MYSQL_Permissions
from schemas.student import MYSQL_Students
from schemas.faculty import MYSQL_Faculty
from typing import Optional
from faker import Faker
import random
fake = Faker()

router = APIRouter(tags=["Students"])

# =============================================================================
# ID FORMAT REFERENCE FOR STUDENTS ENDPOINTS
# =============================================================================
"""
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """

@router.post("/students")
def create_student(
    # Student details
    name: Optional[str] = Form(None),
    age: Optional[int] = Form(None),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    course_id: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    lecturer_id: Optional[str] = Form(None),
    # Credentials for login
    username: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user=Depends(RequirePermission("post_student")),
):
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """


    name = name or fake.name()
    age = age or fake.random_int(min=18, max=25)
    email = email or fake.unique.email()
    phone = phone or fake.numerify(text="+91##########")
    city = city or fake.city()
    
    if not course_id:
        random_teacher = db.query(MYSQL_Faculty).filter(MYSQL_Faculty.is_lecturer == True).first()
        if random_teacher:
            course_id = random_teacher.course_id
            lecturer_id = lecturer_id or random_teacher.id
            
    year = year or fake.random_int(min=1, max=4)
    username = username or fake.user_name()
    password = password or fake.password()
    
    student_data = {
        "name": name,
        "age": age,
        "email": email,
        "phone": phone,
        "city": city,
        "course_id": course_id,
        "year": year,
        "lecturer_id": lecturer_id,
    }
    
    # Create student
    student = create_student_db(db, student_data, auto_commit=False)
    
    # Auto-assign permissions based on STUDENT role
    try:
        create_permissions(db, {
            "username": username,
            "password": password,
            "role": "student",
            "enrollment_id": student.id,
            "faculty_id": None
        }, auto_commit=False)
        db.commit()
        return {
            "id": student.id,
            "name": student.name,
            "email": student.email,
            "username": username,
            "role": "student",
            "message": "Student created successfully with auto-assigned permissions"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/students")
def get_students(
    db:Session=Depends(get_db),
    user:MYSQL_Permissions=Depends(RequirePermission("get_student"))
):
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    if user.role == "student":
        # Students can only see their own record
        student = db.query(MYSQL_Students).filter(MYSQL_Students.id == user.enrollment_id).first()
        return [student] if student else []
    elif user.role == "faculty":
        # Faculty can only see students assigned to them
        faculty = db.query(MYSQL_Faculty).filter(MYSQL_Faculty.id == user.faculty_id).first()
        if not faculty:
            return []
        return db.query(MYSQL_Students).filter(MYSQL_Students.lecturer_id == faculty.id).all()
    else:
        # Admin, principal, HOD can see all
        return get_all_students_db(db)

@router.get("/lecturers")
def get_available_lecturers(
    course_id: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(RequirePermission("get_student")),
):
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    query = db.query(MYSQL_Faculty).filter(MYSQL_Faculty.is_lecturer == True)
    
    if course_id:
        query = query.filter(MYSQL_Faculty.course_id == course_id)
    
    lecturers = query.all()
    
    return [
        {
            "lecturer_id": lecturer.id,
            "name": lecturer.name,
            "email": lecturer.email,
            "course_id": lecturer.course_id,
        }
        for lecturer in lecturers
    ]

@router.get("/students/{student_id}")
def get_student(
    student_id:str,
    db:Session=Depends(get_db),
    user:MYSQL_Permissions=Depends(RequirePermission("get_student"))
):
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    student=get_student_db(db,student_id)
    if not student: 
        raise HTTPException(status_code=404,detail="Student not found")
    
    # Role-based access control
    if user.role == "student":
        if user.enrollment_id != student_id:
            raise HTTPException(status_code=403, detail="You can only view your own record")
    elif user.role == "faculty":
        faculty = db.query(MYSQL_Faculty).filter(MYSQL_Faculty.id == user.faculty_id).first()
        if faculty and student.lecturer_id != faculty.id:
            raise HTTPException(status_code=403, detail="You can only view students assigned to you")
    
    return student

@router.put("/students/{student_id}")
def update_student(
    student_id: str,
    name: Optional[str] = Form(None),
    age: Optional[int] = Form(None),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    course_id: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    lecturer_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user=Depends(RequirePermission("put_student")),
):
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    student_data = {
        "name": name,
        "age": age,
        "email": email,
        "phone": phone,
        "city": city,
        "course_id": course_id,
        "year": year,
        "lecturer_id": lecturer_id,
    }
    student = update_student_db(db, student_id, student_data)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@router.delete("/students/{student_id}")
def delete_student(
    student_id:str,
    db:Session=Depends(get_db),
    user=Depends(RequirePermission("delete_student"))
):
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    if not delete_student_db(db,student_id):
        raise HTTPException(status_code=404,detail="Student not found")
    return {"detail":"Deleted successfully"}
