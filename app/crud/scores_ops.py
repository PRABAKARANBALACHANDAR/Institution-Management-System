from sqlalchemy.orm import Session
from sqlalchemy import func
from schemas.scores import MYSQLStudentScores, PGStudentScores
from database import PG_SessionLocal
from fastapi import HTTPException
import statistics

def create_score(db:Session,student_id:str,semester:int,marks:dict,lecturer_id:str=None)->MYSQLStudentScores:
    score_id=f"{student_id}_Sem{semester}"
    existing=db.query(MYSQLStudentScores).filter(MYSQLStudentScores.id==score_id).first()
    if existing:
        raise HTTPException(status_code=409,detail=f"Score for student {student_id} semester {semester} exists")
    record=MYSQLStudentScores(id=score_id,semester=semester,student_id=student_id,
                               marks=marks,lecturer_id=lecturer_id)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def get_student_scores(db:Session,student_id:str):
    return db.query(MYSQLStudentScores).filter(MYSQLStudentScores.student_id==student_id).all()

def update_score(db:Session,student_id:str,semester:int,marks:dict):
    score_id=f"{student_id}_Sem{semester}"
    record=db.query(MYSQLStudentScores).filter(MYSQLStudentScores.id==score_id).first()
    if not record:
        raise HTTPException(status_code=404,detail="Score not found")
    record.marks=marks
    db.commit()
    db.refresh(record)
    return record

def calculate_avg_marks(db_mysql: Session, student_id: str, semester: int):
    try:
        # Get all marks for this student in this semester
        scores = db_mysql.query(MYSQLStudentScores).filter(
            MYSQLStudentScores.student_id == student_id,
            MYSQLStudentScores.semester == semester
        ).all()
        
        if not scores:
            return
        
        # Calculate average from JSON marks field
        all_marks = []
        for score in scores:
            if score.marks and isinstance(score.marks, dict):
                all_marks.extend(score.marks.values())
        
        if not all_marks:
            avg_marks = 0.0
        else:
            avg_marks = statistics.mean([float(m) for m in all_marks if isinstance(m, (int, float))])
        
        # Update PostgreSQL OLAP database with average marks
        db_pg = PG_SessionLocal()
        try:
            from uuid import UUID
            import uuid
            # Convert student_id to UUID (hashed in real scenario via Airflow)
            student_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, student_id)
            lecturer_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, scores[0].lecturer_id or "unknown")
            
            pg_score = db_pg.query(PGStudentScores).filter(
                PGStudentScores.student_id == student_uuid,
                PGStudentScores.semester == semester
            ).first()
            
            if pg_score:
                pg_score.avg_marks = avg_marks
                db_pg.commit()
            else:
                new_pg_score = PGStudentScores(
                    id=uuid.uuid4(),
                    student_id=student_uuid,
                    lecturer_id=lecturer_uuid,
                    semester=semester,
                    avg_marks=avg_marks
                )
                db_pg.add(new_pg_score)
                db_pg.commit()
        finally:
            db_pg.close()
    except Exception as e:
        # Log but don't fail the request
        print(f"Error calculating avg marks: {e}")
