from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth.dependencies import RequirePermission
from crud.department_ops import create_department_db,get_all_departments_db,get_department_db,update_department_db,delete_department_db
from pydantic import BaseModel
router=APIRouter(tags=["Departments"])

# =============================================================================
# ID FORMAT REFERENCE FOR DEPARTMENT ENDPOINTS
# =============================================================================
"""
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """

from faker import Faker
from pydantic import Field
import random
fake = Faker()

class DepartmentCreate(BaseModel):
    name: str = Field(default_factory=lambda: fake.job()[:20] + " Dept")
    hod_id: str = Field(default_factory=lambda: f"F{random.randint(1000, 9999)}")
    hod_name: str = Field(default_factory=fake.name)

@router.post("/departments")
def create_department(dept:DepartmentCreate,db:Session=Depends(get_db),user=Depends(RequirePermission("post_dept"))):
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    return create_department_db(db,dept.model_dump())

@router.get("/departments")
def get_departments(db:Session=Depends(get_db),user=Depends(RequirePermission("get_dept"))):
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    return get_all_departments_db(db)

@router.get("/departments/{dept_id}")
def get_department(dept_id:str,db:Session=Depends(get_db),user=Depends(RequirePermission("get_dept"))):
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    dept=get_department_db(db,dept_id)
    if not dept: raise HTTPException(status_code=404,detail="Department not found")
    return dept

@router.put("/departments/{dept_id}")
def update_department(dept_id:str,dept_data:DepartmentCreate,db:Session=Depends(get_db),user=Depends(RequirePermission("put_dept"))):
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    dept=update_department_db(db,dept_id,dept_data.model_dump())
    if not dept: raise HTTPException(status_code=404,detail="Department not found")
    return dept

@router.delete("/departments/{dept_id}")
def delete_department(dept_id:str,db:Session=Depends(get_db),user=Depends(RequirePermission("delete_dept"))):
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    if not delete_department_db(db,dept_id):
        raise HTTPException(status_code=404,detail="Department not found")
    return {"detail":"Deleted successfully"}
