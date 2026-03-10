from sqlalchemy.orm import Session
from schemas.student_attendance import MYSQLStudentAttendance
from schemas.faculty_attendance import MYSQLFacultyAttendance
from schemas.student import MYSQL_Students
from datetime import date
from fastapi import HTTPException

def get_students_for_attendance(db:Session,lecturer_id:str,att_date:date)->list:
    """Get list of students assigned to lecturer with their current attendance status for the date."""
    students=db.query(MYSQL_Students).filter(
        MYSQL_Students.lecturer_id==lecturer_id).all()
    result=[]
    for student in students:
        existing=db.query(MYSQLStudentAttendance).filter(
            MYSQLStudentAttendance.student_id==student.id,
            MYSQLStudentAttendance.date==att_date
        ).first()
        result.append({
            "student_id":student.id,
            "student_name":student.name if student else "Unknown",
            "is_present":existing.is_present if existing else False,
            "already_marked":existing is not None,
            "date": str(att_date)
        })
    return result

def validate_attendance_date_not_marked(db:Session, student_id:str, att_date:date, allow_update:bool=False)->bool:
    """
    Validate that attendance for a date hasn't already been marked.
    
    Args:
        db: Database session
        student_id: Student ID
        att_date: Date to check
        allow_update: If False, raise error if already marked. If True, allow updates.
        
    Returns:
        True if validation passes
        
    Raises:
        HTTPException if already marked and allow_update=False
    """
    existing=db.query(MYSQLStudentAttendance).filter(
        MYSQLStudentAttendance.student_id==student_id,
        MYSQLStudentAttendance.date==att_date
    ).first()
    
    if existing and not allow_update:
        raise HTTPException(
            status_code=409,
            detail=f"Attendance already marked for student {student_id} on {att_date}. Use update endpoint to modify."
        )
    return True

def mark_batch_student_attendance(db:Session,lecturer_id:str,att_date:date,rows:list)->dict:
    """
    Mark student attendance in batch.
    
    Returns info about created vs updated records and any validation errors.
    """
    allowed_ids={s.id for s in db.query(MYSQL_Students).filter(
        MYSQL_Students.lecturer_id==lecturer_id).all()}
    
    created=[]
    updated=[]
    errors=[]
    
    for row in rows:
        if row.student_id not in allowed_ids:
            errors.append({
                "student_id": row.student_id,
                "error": f"Student not assigned to you"
            })
            continue
        
        existing=db.query(MYSQLStudentAttendance).filter(
            MYSQLStudentAttendance.student_id==row.student_id,
            MYSQLStudentAttendance.date==att_date
        ).first()
        
        if existing:
            existing.is_present=row.is_present
            db.flush()
            updated.append({
                "student_id": row.student_id,
                "is_present": row.is_present,
                "status": "updated"
            })
        else:
            record=MYSQLStudentAttendance(
                student_id=row.student_id,
                date=att_date,
                is_present=row.is_present,
                marked_by=lecturer_id
            )
            db.add(record)
            db.flush()
            created.append({
                "student_id": row.student_id,
                "is_present": row.is_present,
                "status": "created"
            })
    
    db.commit()
    
    return {
        "date": str(att_date),
        "created": len(created),
        "updated": len(updated),
        "errors": len(errors),
        "created_records": created,
        "updated_records": updated,
        "error_details": errors if errors else None
    }

def mark_faculty_attendance(db:Session,faculty_id:str,att_date:date,is_present:bool)->dict:
    """
    Mark faculty attendance. Returns whether record was created or updated.
    """
    existing=db.query(MYSQLFacultyAttendance).filter(
        MYSQLFacultyAttendance.faculty_id==faculty_id,
        MYSQLFacultyAttendance.date==att_date
    ).first()
    
    if existing:
        existing.is_present=is_present
        db.commit()
        db.refresh(existing)
        return {
            "faculty_id": faculty_id,
            "date": str(att_date),
            "is_present": is_present,
            "status": "updated",
            "message": f"Attendance updated for faculty {faculty_id} on {att_date}"
        }
    else:
        record=MYSQLFacultyAttendance(
            faculty_id=faculty_id,
            date=att_date,
            is_present=is_present
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return {
            "faculty_id": faculty_id,
            "date": str(att_date),
            "is_present": is_present,
            "status": "created",
            "message": f"Attendance marked for faculty {faculty_id} on {att_date}"
        }

def get_student_attendance(db:Session,student_id:str):
    """Get all attendance records for a student."""
    return db.query(MYSQLStudentAttendance).filter(MYSQLStudentAttendance.student_id==student_id).all()

def get_faculty_attendance(db:Session,faculty_id:str):
    """Get all attendance records for faculty."""
    return db.query(MYSQLFacultyAttendance).filter(MYSQLFacultyAttendance.faculty_id==faculty_id).all()
