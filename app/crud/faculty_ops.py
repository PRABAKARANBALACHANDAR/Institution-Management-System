from sqlalchemy.orm import Session
from schemas.faculty import MYSQL_Faculty
from schemas.permissions import MYSQL_Permissions,Roles
from crud.utils import generate_custom_id
from crud.permissions_ops import create_permissions, check_admin_exists, check_principal_exists
from fastapi import HTTPException

def _check_admin_exists(db:Session):
    if not check_admin_exists(db):
        raise HTTPException(status_code=422,
            detail="No admin exists. Add the admin account first.")

def _check_principal_exists(db:Session):
    if not check_principal_exists(db):
        raise HTTPException(status_code=422,
            detail="No principal exists. Add the principal account first.")

def create_faculty_db(
    db:Session,
    faculty_data:dict,
    auto_commit:bool=True
)->MYSQL_Faculty:
    is_principal=faculty_data.get("is_principal",False)
    is_hod=faculty_data.get("is_hod",False)
    is_lecturer=faculty_data.get("is_lecturer",False)
    
    if is_principal:
        _check_admin_exists(db)
        existing_principal = db.query(MYSQL_Faculty).filter(MYSQL_Faculty.is_principal == True).first()
        if existing_principal:
            raise HTTPException(status_code=400, detail="Only 1 principal is allowed for the whole institution.")
    else:
        _check_principal_exists(db)
        
    if is_hod and faculty_data.get("department_id"):
        existing_dept_hod = db.query(MYSQL_Faculty).filter(
            MYSQL_Faculty.is_hod == True, 
            MYSQL_Faculty.department_id == faculty_data["department_id"]
        ).first()
        if existing_dept_hod:
            raise HTTPException(status_code=400, detail="Only 1 HOD is allowed for each department.")
    
    # Set course_id to None for principal/HOD (they don't teach specific courses)
    if is_principal or is_hod:
        faculty_data["course_id"] = None
    
    # Set department_id to None for lecturer (lecturer is teaching, not managing dept)
    if is_lecturer:
        faculty_data["department_id"] = None
    
    new_id=generate_custom_id(db,MYSQL_Faculty,"F")
    db_faculty=MYSQL_Faculty(id=new_id,**faculty_data)
    db.add(db_faculty)
    if auto_commit:
        db.commit()
        db.refresh(db_faculty)
    else:
        db.flush()
    return db_faculty

def get_all_faculty_db(db:Session):
    return db.query(MYSQL_Faculty).all()

def get_faculty_db(db:Session,faculty_id:str):
    return db.query(MYSQL_Faculty).filter(MYSQL_Faculty.id==faculty_id).first()

def update_faculty_db(db:Session,faculty_id:str,update_data:dict):
    faculty=db.query(MYSQL_Faculty).filter(MYSQL_Faculty.id==faculty_id).first()
    if faculty:
        is_p = update_data.get("is_principal", faculty.is_principal)
        is_h = update_data.get("is_hod", faculty.is_hod)
        dept_id = update_data.get("department_id", faculty.department_id)
        
        if is_p and not faculty.is_principal:
            existing_principal = db.query(MYSQL_Faculty).filter(MYSQL_Faculty.is_principal == True).first()
            if existing_principal and existing_principal.id != faculty_id:
                raise HTTPException(status_code=400, detail="Only 1 principal is allowed for the whole institution.")
                
        if is_h and dept_id:
            existing_dept_hod = db.query(MYSQL_Faculty).filter(
                MYSQL_Faculty.is_hod == True, 
                MYSQL_Faculty.department_id == dept_id,
                MYSQL_Faculty.id != faculty_id
            ).first()
            if existing_dept_hod:
                raise HTTPException(status_code=400, detail="Only 1 HOD is allowed for each department.")

        for key,value in update_data.items():
            setattr(faculty,key,value)
        db.commit()
        db.refresh(faculty)
    return faculty

def delete_faculty_db(db:Session,faculty_id:str):
    try:
        faculty=db.query(MYSQL_Faculty).filter(MYSQL_Faculty.id==faculty_id).first()
        if faculty:
            # Delete associated permissions manually to avoid foreign key constraints
            from schemas.permissions import MYSQL_Permissions
            db.query(MYSQL_Permissions).filter(MYSQL_Permissions.faculty_id==faculty_id).delete()
            
            # Nullify assigned lecturers for students
            from schemas.student import MYSQL_Students
            db.query(MYSQL_Students).filter(MYSQL_Students.lecturer_id==faculty_id).update({"lecturer_id": None})
            
            # Nullify HOD for courses
            from schemas.course import MYSQL_Courses
            db.query(MYSQL_Courses).filter(MYSQL_Courses.hod_id==faculty_id).update({"hod_id": None})
            
            # Nullify HOD for departments
            from schemas.departments import MYSQL_Departments
            db.query(MYSQL_Departments).filter(MYSQL_Departments.hod_id==faculty_id).update({"hod_id": None})
            
            db.delete(faculty)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Cannot delete faculty due to existing dependencies: {str(e)}")
