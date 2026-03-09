from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db, PG_SessionLocal, get_pg_db
from auth.dependencies import RequirePermission
from pydantic import BaseModel
from typing import Optional
from crud.analytics_ops import revenue_analysis, student_performance_analysis, faculty_performance_analysis

router=APIRouter(tags=["Analytics"], prefix="/analytics")

class RevenueReportSummary(BaseModel):
    month:int
    year:int
    total_fees_collected:float
    total_salary_paid:float
    net_revenue:float

@router.get("/dashboard", response_model=RevenueReportSummary)
def get_revenue_analysis(
    db_pg: Session = Depends(get_pg_db),
    user=Depends(RequirePermission("get_analytics")),
):
    return revenue_analysis(db_pg)

@router.get("/performance_analysis/students")
def get_student_performance_analysis(
    student_id: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    db_pg: Session = Depends(get_pg_db),
    user=Depends(RequirePermission("get_analytics")),
):
    filters = {}
    if student_id:
        filters["student_id"] = student_id
    if semester:
        filters["semester"] = semester
    
    return student_performance_analysis(db_pg, filters)

@router.get("/performance_analysis/faculty")
def get_faculty_performance_analysis(
    db_pg: Session = Depends(get_pg_db),
    user=Depends(RequirePermission("get_analytics")),
):
    return faculty_performance_analysis(db_pg)