from typing import Annotated, Any, List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from database import get_db
from auth.dependencies import RequirePermission
from schemas.permissions import MYSQL_Permissions
from pydantic import BaseModel

from crud.scores_ops import (
    calculate_avg_marks,
    create_score,
    get_student_scores,
    import_scores_from_csv,
    update_score,
)

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


class ScoreImportResponse(BaseModel):
    filename: str
    created: int
    skipped: int
    failed: int
    processed_rows: int
    subject_columns: List[str]
    errors: List[str]


class ScoreImportBatchResponse(BaseModel):
    created: int
    skipped: int
    failed: int
    processed_rows: int
    files: List[ScoreImportResponse]

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


@router.post("/upload", response_model=ScoreImportBatchResponse)
async def upload_scores_csv(
    files: Annotated[List[UploadFile], File(...)],
    semester: Annotated[int | None, Form()] = None,
    lecturer_id: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
    user: MYSQL_Permissions = Depends(RequirePermission("post_marks")),
):
    """
    Upload one or more CSV files with columns like:
    student_id,math,science
    or student_id,semester,math,science
    Existing student+semester score rows are skipped.
    """
    if not files:
        raise HTTPException(status_code=400, detail="At least one CSV file is required.")

    batch_results: List[ScoreImportResponse] = []
    total_created = 0
    total_skipped = 0
    total_failed = 0

    for file in files:
        filename = file.filename or "uploaded.csv"
        if not filename.lower().endswith(".csv"):
            batch_results.append(
                ScoreImportResponse(
                    filename=filename,
                    created=0,
                    skipped=0,
                    failed=1,
                    processed_rows=1,
                    subject_columns=[],
                    errors=["Only CSV files are supported."],
                )
            )
            total_failed += 1
            continue

        try:
            csv_content = (await file.read()).decode("utf-8-sig")
            result = import_scores_from_csv(
                db,
                csv_content,
                lecturer_id=lecturer_id or user.faculty_id,
                default_semester=semester,
            )
            file_result = ScoreImportResponse(filename=filename, **result)
        except HTTPException as exc:
            detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
            file_result = ScoreImportResponse(
                filename=filename,
                created=0,
                skipped=0,
                failed=1,
                processed_rows=1,
                subject_columns=[],
                errors=[detail],
            )

        batch_results.append(file_result)
        total_created += file_result.created
        total_skipped += file_result.skipped
        total_failed += file_result.failed

    return ScoreImportBatchResponse(
        created=total_created,
        skipped=total_skipped,
        failed=total_failed,
        processed_rows=total_created + total_skipped + total_failed,
        files=batch_results,
    )
