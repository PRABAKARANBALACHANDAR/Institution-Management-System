from sqlalchemy.orm import Session
from sqlalchemy import func
from schemas.fees import PG_Fees
from schemas.salary import PG_Salary
from schemas.scores import PGStudentScores
from schemas.student import PG_Students
from schemas.faculty import PG_Faculty
from database import PG_SessionLocal
import datetime

def get_pg_db():
    return PG_SessionLocal()

def revenue_analysis(db_pg: Session = None):
    if db_pg is None:
        db_pg = get_pg_db()
    
    now = datetime.datetime.now()
    month = now.month
    year = now.year
    
    total_fees = db_pg.query(func.sum(PG_Fees.amount)).filter(
        PG_Fees.month == month,
        PG_Fees.year == year,
        PG_Fees.is_paid == True
    ).scalar() or 0.0
    
    total_salary = db_pg.query(func.sum(PG_Salary.amount)).filter(
        PG_Salary.month == month,
        PG_Salary.year == year,
        PG_Salary.is_paid == True
    ).scalar() or 0.0
    
    return {
        "month": month,
        "year": year,
        "total_fees_collected": float(total_fees),
        "total_salary_paid": float(total_salary),
        "net_revenue": float(total_fees - total_salary)
    }

def student_performance_analysis(db_pg: Session = None, filters: dict = None):
    if db_pg is None:
        db_pg = get_pg_db()
    
    filters = filters or {}
    
    query = db_pg.query(PGStudentScores)
    
    # Apply filters if provided
    if filters.get("student_id"):
        query = query.filter(PGStudentScores.student_id == filters["student_id"])
    if filters.get("semester"):
        query = query.filter(PGStudentScores.semester == filters["semester"])
    
    scores = query.all()
    
    if not scores:
        return []
    
    result = []
    for score in scores:
        student = db_pg.query(PG_Students).filter(PG_Students.id == score.student_id).first()
        result.append({
            "student_id": str(score.student_id),
            "student_name": student.name if student else "Unknown",
            "semester": score.semester,
            "avg_marks": float(score.avg_marks) if score.avg_marks else 0.0,
        })
    return result

def faculty_performance_analysis(db_pg: Session = None, filters: dict = None):
    if db_pg is None:
        db_pg = get_pg_db()
    
    filters = filters or {}
    
    # Get all faculty with their average student marks
    faculties = db_pg.query(PG_Faculty).all()
    
    result = []
    for faculty in faculties:
        # Get avg marks of all students taught by this faculty
        avg_student_marks = db_pg.query(func.avg(PGStudentScores.avg_marks)).filter(
            PGStudentScores.lecturer_id == faculty.id
        ).scalar() or 0.0
        
        result.append({
            "faculty_id": str(faculty.id),
            "faculty_name": faculty.name,
            "avg_student_marks": float(avg_student_marks),
            "performance_score": float(avg_student_marks),  # Can be enhanced with attendance factor
        })
    
    return result
