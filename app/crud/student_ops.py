from sqlalchemy.orm import Session
from schemas.student import MYSQL_Students
from schemas.faculty import MYSQL_Faculty
from crud.utils import generate_custom_id
from crud.permissions_ops import create_permissions
from fastapi import HTTPException

def _check_teacher_exists(db:Session, course_id: str):
    teacher = db.query(MYSQL_Faculty).filter(
        MYSQL_Faculty.course_id == course_id,
        MYSQL_Faculty.is_lecturer == True
    ).first()
    if not teacher:
        raise HTTPException(status_code=422,
            detail=f"No teacher/lecturer exists for course {course_id}. Assign a teacher first.")

def create_student_db(
    db:Session,
    student_data:dict,
    auto_commit:bool=True
)->MYSQL_Students:
    # Validate teacher exists for the course
    course_id = student_data.get("course_id")
    if course_id:
        _check_teacher_exists(db, course_id)
    
    new_id=generate_custom_id(db,MYSQL_Students,"S")
    db_student=MYSQL_Students(id=new_id,**student_data)
    db.add(db_student)
    if auto_commit:
        db.commit()
        db.refresh(db_student)
    else:
        db.flush()
    return db_student

def get_all_students_db(db:Session):
    return db.query(MYSQL_Students).all()

def get_student_db(db:Session,student_id:str):
    return db.query(MYSQL_Students).filter(MYSQL_Students.id==student_id).first()

def update_student_db(db:Session,student_id:str,update_data:dict):
    student=db.query(MYSQL_Students).filter(MYSQL_Students.id==student_id).first()
    if student:
        for key,value in update_data.items():
            setattr(student,key,value)
        db.commit()
        db.refresh(student)
    return student

def delete_student_db(db:Session,student_id:str):
    try:
        student=db.query(MYSQL_Students).filter(MYSQL_Students.id==student_id).first()
        if student:
            # Delete associated permissions manually to avoid foreign key constraints
            from schemas.permissions import MYSQL_Permissions
            db.query(MYSQL_Permissions).filter(MYSQL_Permissions.enrollment_id==student_id).delete()
            
            db.delete(student)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Cannot delete student due to existing dependencies: {str(e)}")
