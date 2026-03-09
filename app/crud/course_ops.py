from sqlalchemy.orm import Session
from fastapi import HTTPException
from schemas.course import MYSQL_Courses
from crud.utils import generate_custom_id

def create_course_db(db:Session,course_data:dict)->MYSQL_Courses:
    if course_data.get("hod_id"):
        existing_course = db.query(MYSQL_Courses).filter(MYSQL_Courses.hod_id == course_data["hod_id"]).first()
        if existing_course:
             raise HTTPException(status_code=400, detail="This HOD is already assigned to another course. Only 1 HOD allowed per course.")

    new_id=generate_custom_id(db,MYSQL_Courses,"C")
    db_course=MYSQL_Courses(id=new_id,**course_data)
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

def get_all_courses_db(db:Session):
    return db.query(MYSQL_Courses).all()

def get_course_db(db:Session,course_id:str):
    return db.query(MYSQL_Courses).filter(MYSQL_Courses.id==course_id).first()

def update_course_db(db:Session,course_id:str,update_data:dict):
    course=db.query(MYSQL_Courses).filter(MYSQL_Courses.id==course_id).first()
    if course:
        if "hod_id" in update_data and update_data["hod_id"] is not None:
            existing_course = db.query(MYSQL_Courses).filter(
                MYSQL_Courses.hod_id == update_data["hod_id"],
                MYSQL_Courses.id != course_id
            ).first()
            if existing_course:
                 raise HTTPException(status_code=400, detail="This HOD is already assigned to another course. Only 1 HOD allowed per course.")


        for key,value in update_data.items():
            setattr(course,key,value)
        db.commit()
        db.refresh(course)
    return course

 
def delete_course_db(db:Session,course_id:str):
    try:
        course=db.query(MYSQL_Courses).filter(MYSQL_Courses.id==course_id).first()
        if course:
            db.delete(course)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Cannot delete course due to existing dependencies: {str(e)}")
