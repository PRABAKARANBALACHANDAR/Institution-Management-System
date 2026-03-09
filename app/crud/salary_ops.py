from sqlalchemy.orm import Session
from schemas.salary import MYSQL_Salary
from schemas.faculty import MYSQL_Faculty
from crud.utils import generate_custom_id
from datetime import date,datetime
from fastapi import HTTPException

def generate_monthly_salary(db:Session,month:int=None,year:int=None):
    now=datetime.now()
    month=month or now.month
    year=year or now.year
    faculty_list=db.query(MYSQL_Faculty).all()
    created=[]
    for f in faculty_list:
        exists=db.query(MYSQL_Salary).filter(
            MYSQL_Salary.faculty_id==f.id,
            MYSQL_Salary.month==month,
            MYSQL_Salary.year==year).first()
        if not exists:
            new_id=generate_custom_id(db,MYSQL_Salary,"SA")
            record=MYSQL_Salary(id=new_id,faculty_id=f.id,amount=f.salary,
                                month=month,year=year,is_paid=False)
            db.add(record)
            created.append(record)
    db.commit()
    return created

def pay_salary(db:Session,salary_id:str)->MYSQL_Salary:
    record=db.query(MYSQL_Salary).filter(MYSQL_Salary.id==salary_id).first()
    if not record:
        raise HTTPException(status_code=404,detail="Salary record not found")
    if record.is_paid:
        raise HTTPException(status_code=409,detail="Salary already paid")
    record.is_paid=True
    record.paid_date=date.today()
    db.commit()
    db.refresh(record)
    return record

def get_faculty_salary(db:Session,faculty_id:str):
    return db.query(MYSQL_Salary).filter(MYSQL_Salary.faculty_id==faculty_id).all()
