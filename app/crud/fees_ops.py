from sqlalchemy.orm import Session
from schemas.fees import MYSQL_Fees
from crud.utils import generate_custom_id
from datetime import date
from fastapi import HTTPException

def create_fee_record(db:Session,fee_data:dict)->MYSQL_Fees:
    new_id=generate_custom_id(db,MYSQL_Fees,"FE")
    db_fee=MYSQL_Fees(id=new_id,is_paid=False,**fee_data)
    db.add(db_fee)
    db.commit()
    db.refresh(db_fee)
    return db_fee

def get_student_fees(db:Session,student_id:str):
    return db.query(MYSQL_Fees).filter(MYSQL_Fees.student_id==student_id).all()

def pay_fee(db:Session,fee_id:str)->MYSQL_Fees:
    db_fee=db.query(MYSQL_Fees).filter(MYSQL_Fees.id==fee_id).first()
    if not db_fee:
        raise HTTPException(status_code=404,detail="Fee record not found")
    if db_fee.is_paid:
        raise HTTPException(status_code=409,detail="Fee already paid")
    db_fee.is_paid=True
    db_fee.paid_date=date.today()
    db.commit()
    db.refresh(db_fee)
    return db_fee
