from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth.dependencies import RequirePermission
from pydantic import BaseModel
from typing import List,Optional
from datetime import date,datetime
from crud.salary_ops import generate_monthly_salary,pay_salary,get_faculty_salary

router=APIRouter(tags=["Salary"],prefix="/salary")

class SalaryGenerateRequest(BaseModel):
    month:Optional[int]=None
    year:Optional[int]=None

class SalaryResponse(BaseModel):
    id:str
    faculty_id:str
    amount:int
    month:int
    year:int
    is_paid:bool
    paid_date:Optional[date]=None
    created_at:datetime
    class Config:
        from_attributes=True

@router.post("/generate")
def generate_salary(req:SalaryGenerateRequest=SalaryGenerateRequest(),
                    db:Session=Depends(get_db),
                    user=Depends(RequirePermission("post_salary"))):
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    records=generate_monthly_salary(db,req.month,req.year)
    return{"message":f"Generated {len(records)} salary records"}

@router.get("/{faculty_id}",response_model=List[SalaryResponse])
def get_salary(faculty_id:str,db:Session=Depends(get_db),
               user=Depends(RequirePermission("get_salary"))):
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    return get_faculty_salary(db,faculty_id)

@router.put("/{salary_id}/pay",response_model=SalaryResponse)
def pay_salary_endpoint(salary_id:str,db:Session=Depends(get_db),
                        user=Depends(RequirePermission("put_salary"))):
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    return pay_salary(db,salary_id)
