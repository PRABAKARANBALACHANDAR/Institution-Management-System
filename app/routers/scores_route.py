from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth.dependencies import RequirePermission,get_current_user
from schemas.permissions import MYSQL_Permissions
from pydantic import BaseModel
from typing import List,Any,Optional
from crud.scores_ops import create_score,get_student_scores,update_score, calculate_avg_marks

router=APIRouter(tags=["Scores / Marks"],prefix="/scores")

class ScoreCreate(BaseModel):
    student_id:str
    semester:int
    marks:Any

class ScoreUpdate(BaseModel):
    marks:Any

class ScoreResponse(BaseModel):
    id:str
    student_id:str
    semester:int
    marks:Any
    class Config:
        from_attributes=True

@router.post("/",response_model=ScoreResponse)
def post_score(
    data:ScoreCreate,
    db:Session=Depends(get_db),
    user:MYSQL_Permissions=Depends(RequirePermission("post_marks"))
):
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    score = create_score(db,data.student_id,data.semester,data.marks,user.faculty_id)
    # Calculate average marks for performance metrics
    calculate_avg_marks(db, data.student_id, data.semester)
    return score

@router.get("/{student_id}",response_model=List[ScoreResponse])
def get_scores(
    student_id:str,
    db:Session=Depends(get_db),
    user:MYSQL_Permissions=Depends(RequirePermission("get_marks"))
):
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    # Students can only see their own scores
    if user.role == "student" and user.enrollment_id != student_id:
        raise HTTPException(status_code=403, detail="You can only view your own scores")
    
    return get_student_scores(db, student_id)

@router.put("/{student_id}/{semester}",response_model=ScoreResponse)
def put_score(
    student_id:str,
    semester:int,
    data:ScoreUpdate,
    db:Session=Depends(get_db),
    user:MYSQL_Permissions=Depends(RequirePermission("put_marks"))
):
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    score = update_score(db, student_id, semester, data.marks)
    # Recalculate average marks for performance metrics
    calculate_avg_marks(db, student_id, semester)
    return score