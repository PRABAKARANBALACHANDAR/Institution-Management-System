from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth.dependencies import RequirePermission,get_current_user
from pydantic import BaseModel
from typing import List,Optional
from datetime import date
from crud.leave_req_ops import (create_leave_request,get_all_leave_requests,
                                 get_leave_requests_by_role,update_leave_status,escalate_leave)

router=APIRouter(tags=["Leave Requests"],prefix="/leave-requests")

class LeaveCreate(BaseModel):
    role:str
    role_id:str
    leave_type:str
    from_date:date
    to_date:date
    reason:str

class LeaveStatusUpdate(BaseModel):
    status:str
    escalated_to:Optional[str]=None

class LeaveResponse(BaseModel):
    id:str
    role:str
    role_id:str
    leave_type:str
    from_date:date
    to_date:date
    reason:str
    status:str
    approved_by:Optional[str]=None
    escalated_to:Optional[str]=None
    class Config:
        from_attributes=True

@router.post("/",response_model=LeaveResponse)
def create_leave(data:LeaveCreate,db:Session=Depends(get_db),
                 user=Depends(RequirePermission("post_leave_req"))):
    return create_leave_request(db,data.model_dump())

@router.get("/",response_model=List[LeaveResponse])
def list_all_leaves(db:Session=Depends(get_db),user=Depends(RequirePermission("get_leave_req"))):
    return get_all_leave_requests(db)

@router.get("/{role}/{role_id}",response_model=List[LeaveResponse])
def get_my_leaves(role:str,role_id:str,db:Session=Depends(get_db),
                  user=Depends(RequirePermission("get_leave_req"))):
    return get_leave_requests_by_role(db,role,role_id)

@router.put("/{leave_id}",response_model=LeaveResponse)
def update_leave(leave_id:str,data:LeaveStatusUpdate,db:Session=Depends(get_db),
                 user=Depends(RequirePermission("put_leave_req"))):
    if data.escalated_to:
        return escalate_leave(db,leave_id,data.escalated_to)
    return update_leave_status(db,leave_id,data.status,user.faculty_id)
