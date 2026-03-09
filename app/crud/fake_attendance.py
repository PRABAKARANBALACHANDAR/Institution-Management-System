from sqlalchemy.orm import Session
from schemas.student import MYSQL_Students, PG_Students
from schemas.faculty import MYSQL_Faculty, PG_Faculty
from schemas.student_attendance import MYSQLStudentAttendance, PGStudentAttendance
from schemas.faculty_attendance import MYSQLFacultyAttendance, PGFacultyAttendance
from datetime import date
from uuid import uuid4, uuid5, NAMESPACE_DNS
from fastapi import HTTPException


def sync_student_attendance_to_pg(mysql_db: Session, pg_db: Session, att_date: date = None) -> dict:

    if att_date is None:
        att_date = date.today()
    
    # Get all student attendance from MySQL for the date
    mysql_records = mysql_db.query(MYSQLStudentAttendance).filter(
        MYSQLStudentAttendance.date == att_date
    ).all()
    
    if not mysql_records:
        return {"status": "no_records", "date": str(att_date), "synced": 0}
    
    synced_count = 0
    skipped_count = 0
    
    for att in mysql_records:
        # Get the student from MySQL
        student = mysql_db.query(MYSQL_Students).filter(
            MYSQL_Students.id == att.student_id
        ).first()
        
        if not student:
            skipped_count += 1
            continue
        
        # Convert student ID to UUID using the same logic
        pg_student_id = uuid5(NAMESPACE_DNS, student.id)
        
        # Check if this attendance already exists in PG
        existing = pg_db.query(PGStudentAttendance).filter(
            PGStudentAttendance.student_id == pg_student_id,
            PGStudentAttendance.date == att_date
        ).first()
        
        if existing:
            # Update existing record if present status changed
            existing.is_present = att.is_present
            skipped_count += 1
        else:
            # Create new attendance record in PG
            pg_record = PGStudentAttendance(
                id=uuid4(),
                student_id=pg_student_id,
                date=att_date,
                is_present=att.is_present
            )
            pg_db.add(pg_record)
            synced_count += 1
    
    pg_db.commit()
    return {
        "status": "synced",
        "date": str(att_date),
        "synced": synced_count,
        "updated": skipped_count
    }


def sync_faculty_attendance_to_pg(mysql_db: Session, pg_db: Session, att_date: date = None) -> dict:
    """
    Sync faculty attendance from MySQL to PostgreSQL.
    
    Validates that:
    1. Attendance records exist in MySQL for the date
    2. Attendance for that date doesn't already exist in PG
    
    Returns count of synced records
    """
    if att_date is None:
        att_date = date.today()
    
    # Get all faculty attendance from MySQL for the date
    mysql_records = mysql_db.query(MYSQLFacultyAttendance).filter(
        MYSQLFacultyAttendance.date == att_date
    ).all()
    
    if not mysql_records:
        return {"status": "no_records", "date": str(att_date), "synced": 0}
    
    synced_count = 0
    skipped_count = 0
    
    for att in mysql_records:
        # Get the faculty from MySQL
        faculty = mysql_db.query(MYSQL_Faculty).filter(
            MYSQL_Faculty.id == att.faculty_id
        ).first()
        
        if not faculty:
            skipped_count += 1
            continue
        
        # Convert faculty ID to UUID using the same logic
        pg_faculty_id = uuid5(NAMESPACE_DNS, faculty.id)
        
        # Check if this attendance already exists in PG
        existing = pg_db.query(PGFacultyAttendance).filter(
            PGFacultyAttendance.faculty_id == pg_faculty_id,
            PGFacultyAttendance.date == att_date
        ).first()
        
        if existing:
            # Update existing record if present status changed
            existing.is_present = att.is_present
            skipped_count += 1
        else:
            # Create new attendance record in PG
            pg_record = PGFacultyAttendance(
                id=uuid4(),
                faculty_id=pg_faculty_id,
                date=att_date,
                is_present=att.is_present
            )
            pg_db.add(pg_record)
            synced_count += 1
    
    pg_db.commit()
    return {
        "status": "synced",
        "date": str(att_date),
        "synced": synced_count,
        "updated": skipped_count
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

