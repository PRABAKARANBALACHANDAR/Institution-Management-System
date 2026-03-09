from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from database import get_db
from auth.dependencies import RequirePermission
from crud.faculty_ops import create_faculty_db
from crud.faculty_ops import get_all_faculty_db, get_faculty_db, update_faculty_db, delete_faculty_db
from crud.permissions_ops import create_permissions
from typing import Optional
from faker import Faker
import random
fake = Faker()

router = APIRouter(tags=["Faculty"])

@router.post("/faculty")
def create_faculty(
    # Faculty details
    name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    is_lecturer: bool = Form(False),
    is_hod: bool = Form(False),
    is_principal: bool = Form(False),
    salary: Optional[int] = Form(None),
    department_id: Optional[str] = Form(None),
    course_id: Optional[str] = Form(None),
    # Credentials for login
    username: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user=Depends(RequirePermission("post_faculty")),
):
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """

    name = name or fake.name()
    email = email or fake.unique.email()
    phone = phone or fake.numerify(text="+91##########")
    city = city or fake.city()
    salary = salary or fake.random_int(min=40000, max=150000)
    username = username or fake.user_name()
    password = password or fake.password()
    faculty_data = {
        "name": name,
        "email": email,
        "phone": phone,
        "city": city,
        "is_lecturer": is_lecturer,
        "is_hod": is_hod,
        "is_principal": is_principal,
        "salary": salary,
        "department_id": department_id,
        "course_id": course_id,
    }
    
    # Determine faculty role based on flags
    if is_principal:
        faculty_role = "principal"
    elif is_hod:
        faculty_role = "hod"
    else:
        faculty_role = "faculty"
    
    # Create faculty
    faculty = create_faculty_db(db, faculty_data, auto_commit=False)
    
    # Auto-assign permissions based on faculty role
    try:
        create_permissions(db, {
            "username": username,
            "password": password,
            "role": faculty_role,
            "faculty_id": faculty.id,
            "enrollment_id": None
        }, auto_commit=False)
        db.commit()
        return {
            "id": faculty.id,
            "name": faculty.name,
            "email": faculty.email,
            "username": username,
            "role": faculty_role,
            "message": f"Faculty created successfully with auto-assigned {faculty_role} permissions"
        }
    except Exception:
        db.rollback()
        raise

@router.get("/faculty", response_model=None)
def get_faculty_list(db: Session = Depends(get_db), user=Depends(RequirePermission("get_faculty"))):
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    return get_all_faculty_db(db)

@router.get("/faculty/{faculty_id}", response_model=None)
def get_faculty(faculty_id: str, db: Session = Depends(get_db), user=Depends(RequirePermission("get_faculty"))):
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    faculty = get_faculty_db(db, faculty_id)
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty not found")
    return faculty

@router.put("/faculty/{faculty_id}", response_model=None)
def update_faculty(
    faculty_id: str,
    name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    is_lecturer: bool = Form(False),
    is_hod: bool = Form(False),
    is_principal: bool = Form(False),
    salary: Optional[int] = Form(None),
    department_id: Optional[str] = Form(None),
    course_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user=Depends(RequirePermission("put_faculty")),
):
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    faculty_data = {
        "name": name,
        "email": email,
        "phone": phone,
        "city": city,
        "is_lecturer": is_lecturer,
        "is_hod": is_hod,
        "is_principal": is_principal,
        "salary": salary,
        "department_id": department_id,
        "course_id": course_id,
    }
    faculty = update_faculty_db(db, faculty_id, faculty_data)
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty not found")
    return faculty

@router.delete("/faculty/{faculty_id}", response_model=None)
def delete_faculty(faculty_id: str, db: Session = Depends(get_db), user=Depends(RequirePermission("delete_faculty"))):
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    if not delete_faculty_db(db, faculty_id):
        raise HTTPException(status_code=404, detail="Faculty not found")
    return {"detail": "Deleted successfully"}
