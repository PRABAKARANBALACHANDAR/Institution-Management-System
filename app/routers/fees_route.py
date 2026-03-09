from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth.dependencies import RequirePermission
from pydantic import BaseModel
from typing import List,Optional
from datetime import date,datetime
from crud.fees_ops import create_fee_record,get_student_fees,pay_fee

router=APIRouter(tags=["Fees"],prefix="/fees")

class FeeCreate(BaseModel):
    student_id:str
    amount:int
    month:int
    year:int

class FeeResponse(BaseModel):
    id:str
    student_id:str
    amount:int
    month:int
    year:int
    is_paid:bool
    paid_date:Optional[date]=None
    created_at:datetime
    class Config:
        from_attributes=True

@router.post("/",response_model=FeeResponse)
def create_fee(data:FeeCreate,db:Session=Depends(get_db),
               user=Depends(RequirePermission("post_fees"))):
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    return create_fee_record(db,data.model_dump())

@router.get("/{student_id}",response_model=List[FeeResponse])
def get_fees(student_id:str,db:Session=Depends(get_db),
             user=Depends(RequirePermission("get_fees"))):
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    return get_student_fees(db,student_id)

@router.put("/{fee_id}/pay",response_model=FeeResponse)
def pay_fee_endpoint(fee_id:str,db:Session=Depends(get_db),
                     user=Depends(RequirePermission("put_fees"))):
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    return pay_fee(db,fee_id)
