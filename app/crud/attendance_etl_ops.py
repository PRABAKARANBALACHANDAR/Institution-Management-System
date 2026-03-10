from sqlalchemy.orm import Session
from schemas.student import MYSQL_Students, PG_Students
from schemas.faculty import MYSQL_Faculty, PG_Faculty
from schemas.student_attendance import MYSQLStudentAttendance, PGStudentAttendance
from schemas.faculty_attendance import MYSQLFacultyAttendance, PGFacultyAttendance
from datetime import date
from uuid import uuid4, uuid5, NAMESPACE_DNS
from fastapi import HTTPException


def sync_student_attendance_to_pg(mysql_db: Session, pg_db: Session, att_date: date = None) -> dict:
    
    # If att_date is None, sync ALL records (great for historical catch-up after faker runs)
    query = mysql_db.query(MYSQLStudentAttendance)
    if att_date is not None:
        query = query.filter(MYSQLStudentAttendance.date == att_date)
        
    mysql_records = query.all()
    
    if not mysql_records:
        return {"status": "no_records", "date": str(att_date) if att_date else "ALL", "synced": 0}
    
    # Bulk maps to prevent N+1 queries
    all_students = mysql_db.query(MYSQL_Students).all()
    student_uuid_map = {s.id: uuid5(NAMESPACE_DNS, s.id) for s in all_students}
    
    # Get existing PG records in bulk to prevent N+1 lookups
    pg_query = pg_db.query(PGStudentAttendance.student_id, PGStudentAttendance.date)
    if att_date is not None:
        pg_query = pg_query.filter(PGStudentAttendance.date == att_date)
        
    existing_pg_keys = {(str(r[0]), r[1]) for r in pg_query.all()}
    
    synced_count = 0
    skipped_count = 0
    new_records = []
    
    for att in mysql_records:
        pg_student_id = student_uuid_map.get(att.student_id)
        if not pg_student_id:
            skipped_count += 1
            continue
            
        key = (str(pg_student_id), att.date)
        
        if key in existing_pg_keys:
            # We skip full updates in bulk mode to keep it fast
            skipped_count += 1
        else:
            new_records.append(PGStudentAttendance(
                id=uuid4(),
                student_id=pg_student_id,
                date=att.date,
                is_present=att.is_present
            ))
            existing_pg_keys.add(key)
            synced_count += 1
            
    if new_records:
        pg_db.bulk_save_objects(new_records)
        pg_db.commit()
        
    return {
        "status": "synced",
        "date": str(att_date) if att_date else "ALL",
        "synced": synced_count,
        "skipped": skipped_count
    }


def sync_faculty_attendance_to_pg(mysql_db: Session, pg_db: Session, att_date: date = None) -> dict:
    
    query = mysql_db.query(MYSQLFacultyAttendance)
    if att_date is not None:
        query = query.filter(MYSQLFacultyAttendance.date == att_date)
        
    mysql_records = query.all()
    
    if not mysql_records:
        return {"status": "no_records", "date": str(att_date) if att_date else "ALL", "synced": 0}
    
    all_facs = mysql_db.query(MYSQL_Faculty).all()
    fac_uuid_map = {f.id: uuid5(NAMESPACE_DNS, f.id) for f in all_facs}
    
    pg_query = pg_db.query(PGFacultyAttendance.faculty_id, PGFacultyAttendance.date)
    if att_date is not None:
        pg_query = pg_query.filter(PGFacultyAttendance.date == att_date)
        
    existing_pg_keys = {(str(r[0]), r[1]) for r in pg_query.all()}
    
    synced_count = 0
    skipped_count = 0
    new_records = []
    
    for att in mysql_records:
        pg_fac_id = fac_uuid_map.get(att.faculty_id)
        if not pg_fac_id:
            skipped_count += 1
            continue
            
        key = (str(pg_fac_id), att.date)
        
        if key in existing_pg_keys:
            skipped_count += 1
        else:
            new_records.append(PGFacultyAttendance(
                id=uuid4(),
                faculty_id=pg_fac_id,
                date=att.date,
                is_present=att.is_present
            ))
            existing_pg_keys.add(key)
            synced_count += 1
            
    if new_records:
        pg_db.bulk_save_objects(new_records)
        pg_db.commit()
        
    return {
        "status": "synced",
        "date": str(att_date) if att_date else "ALL",
        "synced": synced_count,
        "skipped": skipped_count
    }


def validate_attendance_not_marked(db: Session, entity_id: str, entity_type: str, att_date: date) -> bool:
    """
    Validate that attendance for a specific date hasn't already been marked.
    
    Args:
        db: Database session
        entity_id: Student or Faculty ID
        entity_type: 'student' or 'faculty'
        att_date: Date to check
        
    Returns:
        True if attendance NOT already marked, False if already exists
        
    Raises:
        HTTPException if attendance already exists
    """
    if entity_type == "student":
        existing = db.query(MYSQLStudentAttendance).filter(
            MYSQLStudentAttendance.student_id == entity_id,
            MYSQLStudentAttendance.date == att_date
        ).first()
    elif entity_type == "faculty":
        existing = db.query(MYSQLFacultyAttendance).filter(
            MYSQLFacultyAttendance.faculty_id == entity_id,
            MYSQLFacultyAttendance.date == att_date
        ).first()
    else:
        raise ValueError("entity_type must be 'student' or 'faculty'")
    
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Attendance already marked for this {entity_type} on {att_date}"
        )
    
    return True

