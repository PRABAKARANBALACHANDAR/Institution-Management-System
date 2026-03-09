from sqlalchemy.orm import Session
from fastapi import HTTPException
from schemas.departments import MYSQL_Departments
from crud.utils import generate_custom_id

def create_department_db(db:Session,dept_data:dict)->MYSQL_Departments:
    if dept_data.get("hod_id"):
        existing_dept = db.query(MYSQL_Departments).filter(MYSQL_Departments.hod_id == dept_data["hod_id"]).first()
        if existing_dept:
             raise HTTPException(status_code=400, detail="This HOD is already assigned to another department. Only 1 HOD allowed per department.")
             
    new_id=generate_custom_id(db,MYSQL_Departments,"D")
    db_dept=MYSQL_Departments(id=new_id,**dept_data)
    db.add(db_dept)
    db.commit()
    db.refresh(db_dept)
    return db_dept

def get_all_departments_db(db:Session):
    return db.query(MYSQL_Departments).all()

def get_department_db(db:Session,dept_id:str):
    return db.query(MYSQL_Departments).filter(MYSQL_Departments.id==dept_id).first()

def update_department_db(db:Session,dept_id:str,update_data:dict):
    dept=db.query(MYSQL_Departments).filter(MYSQL_Departments.id==dept_id).first()
    if dept:
        if "hod_id" in update_data and update_data["hod_id"] is not None:
            existing_dept = db.query(MYSQL_Departments).filter(
                MYSQL_Departments.hod_id == update_data["hod_id"],
                MYSQL_Departments.id != dept_id
            ).first()
            if existing_dept:
                 raise HTTPException(status_code=400, detail="This HOD is already assigned to another department. Only 1 HOD allowed per department.")
                 
        for key,value in update_data.items():
            setattr(dept,key,value)
        db.commit()
        db.refresh(dept)
    return dept

 
def delete_department_db(db:Session,dept_id:str):
    try:
        dept=db.query(MYSQL_Departments).filter(MYSQL_Departments.id==dept_id).first()
        if dept:
            db.delete(dept)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Cannot delete department due to existing dependencies: {str(e)}")
