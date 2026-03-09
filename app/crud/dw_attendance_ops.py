from datetime import date
from uuid import UUID, uuid4
from sqlalchemy.orm import Session

from schemas.student import PG_Students
from schemas.faculty import PG_Faculty
from schemas.student_attendance import PGStudentAttendance
from schemas.faculty_attendance import PGFacultyAttendance


def get_pg_students_for_attendance(pg_db:Session,att_date:date)->list:
    students=pg_db.query(PG_Students).all()
    result=[]
    for s in students:
        existing=pg_db.query(PGStudentAttendance).filter(
            PGStudentAttendance.student_id==s.id,
            PGStudentAttendance.date==att_date
        ).first()
        result.append({
            "student_id":str(s.id),
            "student_name":s.name,
            "is_present":existing.is_present if existing else False,
            "already_marked":existing is not None
        })
    return result


def get_pg_faculty_for_attendance(pg_db:Session,att_date:date)->list:
    faculty=pg_db.query(PG_Faculty).all()
    result=[]
    for f in faculty:
        existing=pg_db.query(PGFacultyAttendance).filter(
            PGFacultyAttendance.faculty_id==f.id,
            PGFacultyAttendance.date==att_date
        ).first()
        result.append({
            "faculty_id":str(f.id),
            "faculty_name":f.name,
            "is_present":existing.is_present if existing else False,
            "already_marked":existing is not None
        })
    return result


def mark_pg_student_attendance_batch(pg_db:Session,att_date:date,rows:list)->list:
    saved=[]
    for row in rows:
        student_uuid=UUID(row.student_id)
        existing=pg_db.query(PGStudentAttendance).filter(
            PGStudentAttendance.student_id==student_uuid,
            PGStudentAttendance.date==att_date
        ).first()
        if existing:
            existing.is_present=row.is_present
            saved.append(existing)
            continue
        record=PGStudentAttendance(
            id=uuid4(),
            student_id=student_uuid,
            date=att_date,
            is_present=row.is_present
        )
        pg_db.add(record)
        saved.append(record)
    pg_db.commit()
    return saved


def mark_pg_faculty_attendance_batch(pg_db:Session,att_date:date,rows:list)->list:
    saved=[]
    for row in rows:
        faculty_uuid=UUID(row.faculty_id)
        existing=pg_db.query(PGFacultyAttendance).filter(
            PGFacultyAttendance.faculty_id==faculty_uuid,
            PGFacultyAttendance.date==att_date
        ).first()
        if existing:
            existing.is_present=row.is_present
            saved.append(existing)
            continue
        record=PGFacultyAttendance(
            id=uuid4(),
            faculty_id=faculty_uuid,
            date=att_date,
            is_present=row.is_present
        )
        pg_db.add(record)
        saved.append(record)
    pg_db.commit()
    return saved
