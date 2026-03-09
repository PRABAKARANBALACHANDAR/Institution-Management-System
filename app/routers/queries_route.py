from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth.dependencies import RequirePermission,get_current_user
from schemas.permissions import MYSQL_Permissions
from pydantic import BaseModel
from typing import List
from crud.queries_ops import create_query,get_all_queries,get_queries_by_role,answer_query

router=APIRouter(tags=["Queries"],prefix="/queries")

class QueryCreate(BaseModel):
    role:str
    role_id:str
    query:str

class QueryAnswer(BaseModel):
    answer:str

class QueryResponse(BaseModel):
    id:str
    role:str
    role_id:str
    query:str
    answer:str|None=None
    answered_by:str|None=None
    class Config:
        from_attributes=True

@router.post("/",response_model=QueryResponse)
def post_query(data:QueryCreate,db:Session=Depends(get_db),
               user=Depends(RequirePermission("post_queries"))):
    return create_query(db,data.model_dump())

@router.get("/",response_model=List[QueryResponse])
def list_queries(
    db:Session=Depends(get_db),
    user:MYSQL_Permissions=Depends(RequirePermission("get_queries"))
):
    if user.role in ["admin", "principal"]:
        # Admin and principal can see all queries
        return get_all_queries(db)
    else:
        # Teachers and students can only see their own queries
        return get_queries_by_role(db, user.role, user.enrollment_id or user.faculty_id)

@router.get("/{role}/{role_id}",response_model=List[QueryResponse])
def get_role_queries(
    role:str,
    role_id:str,
    db:Session=Depends(get_db),
    user:MYSQL_Permissions=Depends(RequirePermission("get_queries"))
):
    # Only admins/principals can view other people's queries
    if user.role not in ["admin", "principal"]:
        if role != user.role or role_id != (user.enrollment_id or user.faculty_id):
            raise HTTPException(status_code=403, detail="Access denied")
    
    return get_queries_by_role(db, role, role_id)

@router.put("/{query_id}",response_model=QueryResponse)
def answer_query_endpoint(
    query_id:str,
    data:QueryAnswer,
    db:Session=Depends(get_db),
    user:MYSQL_Permissions=Depends(get_current_user)
):
    if user.role not in ["admin", "principal"]:
        raise HTTPException(status_code=403, detail="Only admin/principal can answer queries")
    
    return answer_query(db, query_id, data.answer, user.username)
