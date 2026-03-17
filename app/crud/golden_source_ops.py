from __future__ import annotations

from datetime import datetime
from uuid import NAMESPACE_DNS, uuid4, uuid5
import json

from sqlalchemy.orm import Session

from schemas.course import MYSQL_Courses, PG_Courses
from schemas.departments import MYSQL_Departments, PG_Departments
from schemas.faculty import MYSQL_Faculty, PG_Faculty
from schemas.faculty_attendance import MYSQLFacultyAttendance, PGFacultyAttendance
from schemas.fees import MYSQL_Fees, PG_Fees
from schemas.golden_source import (
    MYSQL_ETL_Watermark,
    MYSQL_Gold_Courses,
    MYSQL_Gold_Departments,
    MYSQL_Gold_Faculty,
    MYSQL_Gold_FacultyAttendance,
    MYSQL_Gold_Fees,
    MYSQL_Gold_Salary,
    MYSQL_Gold_Snapshot_Batch,
    MYSQL_Gold_Snapshot_Courses,
    MYSQL_Gold_Snapshot_Departments,
    MYSQL_Gold_Snapshot_Faculty,
    MYSQL_Gold_Snapshot_FacultyAttendance,
    MYSQL_Gold_Snapshot_Fees,
    MYSQL_Gold_Snapshot_Salary,
    MYSQL_Gold_Snapshot_StudentAttendance,
    MYSQL_Gold_Snapshot_StudentScores,
    MYSQL_Gold_Snapshot_Students,
    MYSQL_Gold_StudentAttendance,
    MYSQL_Gold_StudentScores,
    MYSQL_Gold_Students,
)
from schemas.salary import MYSQL_Salary, PG_Salary
from schemas.scores import MYSQLStudentScores, PGStudentScores
from schemas.student import MYSQL_Students, PG_Students
from schemas.student_attendance import MYSQLStudentAttendance, PGStudentAttendance


ENTITY_CONFIG = {
    "departments": {
        "source_model": MYSQL_Departments,
        "gold_model": MYSQL_Gold_Departments,
        "snapshot_model": MYSQL_Gold_Snapshot_Departments,
        "watermark_field": "updated_at",
        "payload_fields": ["name", "hod_id", "hod_name"],
    },
    "courses": {
        "source_model": MYSQL_Courses,
        "gold_model": MYSQL_Gold_Courses,
        "snapshot_model": MYSQL_Gold_Snapshot_Courses,
        "watermark_field": "updated_at",
        "payload_fields": ["name", "domain", "hod_id"],
    },
    "faculty": {
        "source_model": MYSQL_Faculty,
        "gold_model": MYSQL_Gold_Faculty,
        "snapshot_model": MYSQL_Gold_Snapshot_Faculty,
        "watermark_field": "updated_at",
        "payload_fields": ["name", "email", "phone", "city", "is_lecturer", "is_hod", "is_principal", "salary", "course_id", "department_id"],
    },
    "students": {
        "source_model": MYSQL_Students,
        "gold_model": MYSQL_Gold_Students,
        "snapshot_model": MYSQL_Gold_Snapshot_Students,
        "watermark_field": "updated_at",
        "payload_fields": ["name", "age", "email", "phone", "city", "course_id", "lecturer_id", "year"],
    },
    "student_attendance": {
        "source_model": MYSQLStudentAttendance,
        "gold_model": MYSQL_Gold_StudentAttendance,
        "snapshot_model": MYSQL_Gold_Snapshot_StudentAttendance,
        "watermark_field": "updated_at",
        "payload_fields": ["student_id", "date", "is_present", "marked_by"],
    },
    "faculty_attendance": {
        "source_model": MYSQLFacultyAttendance,
        "gold_model": MYSQL_Gold_FacultyAttendance,
        "snapshot_model": MYSQL_Gold_Snapshot_FacultyAttendance,
        "watermark_field": "updated_at",
        "payload_fields": ["faculty_id", "date", "is_present"],
    },
    "scores": {
        "source_model": MYSQLStudentScores,
        "gold_model": MYSQL_Gold_StudentScores,
        "snapshot_model": MYSQL_Gold_Snapshot_StudentScores,
        "watermark_field": "updated_at",
        "payload_fields": ["semester", "student_id", "lecturer_id", "marks"],
    },
    "fees": {
        "source_model": MYSQL_Fees,
        "gold_model": MYSQL_Gold_Fees,
        "snapshot_model": MYSQL_Gold_Snapshot_Fees,
        "watermark_field": "updated_at",
        "payload_fields": ["student_id", "amount", "month", "year", "is_paid", "paid_date"],
    },
    "salary": {
        "source_model": MYSQL_Salary,
        "gold_model": MYSQL_Gold_Salary,
        "snapshot_model": MYSQL_Gold_Snapshot_Salary,
        "watermark_field": "updated_at",
        "payload_fields": ["faculty_id", "amount", "month", "year", "is_paid", "paid_date"],
    },
}

def _get_row_watermark(row, preferred_field: str) -> datetime | None:
    return getattr(row, preferred_field, None) or getattr(row, "created_at", None)


def _row_payload(row, payload_fields: list[str]) -> dict:
    payload = {field: getattr(row, field, None) for field in payload_fields}
    payload["source_created_at"] = getattr(row, "created_at", None)
    payload["source_updated_at"] = getattr(row, "updated_at", None)
    payload["extracted_at"] = datetime.now()
    return payload


def extract_incremental_to_golden(mysql_db: Session) -> dict:
    result = {"counts": {}, "watermarks": {}}

    for entity_name, config in ENTITY_CONFIG.items():
        source_model = config["source_model"]
        gold_model = config["gold_model"]
        watermark_field = config["watermark_field"]
        payload_fields = config["payload_fields"]

        watermark_state = mysql_db.query(MYSQL_ETL_Watermark).filter(MYSQL_ETL_Watermark.entity_name == entity_name).first()
        last_success_at = watermark_state.last_success_at if watermark_state else None

        query = mysql_db.query(source_model)
        if last_success_at is not None:
            preferred_column = getattr(source_model, watermark_field, None)
            created_column = getattr(source_model, "created_at", None)
            if preferred_column is not None and created_column is not None:
                query = query.filter((preferred_column > last_success_at) | (created_column > last_success_at))
            elif preferred_column is not None:
                query = query.filter(preferred_column > last_success_at)
            elif created_column is not None:
                query = query.filter(created_column > last_success_at)

        rows = query.all()
        max_watermark = last_success_at

        for row in rows:
            payload = _row_payload(row, payload_fields)
            existing = mysql_db.query(gold_model).filter(gold_model.source_id == row.id).first()
            if existing:
                for key, value in payload.items():
                    setattr(existing, key, value)
            else:
                mysql_db.add(gold_model(source_id=row.id, **payload))

            row_watermark = _get_row_watermark(row, watermark_field)
            if row_watermark is not None and (max_watermark is None or row_watermark > max_watermark):
                max_watermark = row_watermark

        result["counts"][entity_name] = len(rows)
        result["watermarks"][entity_name] = max_watermark.isoformat() if max_watermark else None

    mysql_db.commit()
    return result


def create_snapshot_batch(mysql_db: Session) -> dict:
    batch_id = uuid4().hex
    counts = {}

    for entity_name, config in ENTITY_CONFIG.items():
        gold_model = config["gold_model"]
        snapshot_model = config["snapshot_model"]
        rows = mysql_db.query(gold_model).all()
        counts[entity_name] = len(rows)

        for row in rows:
            snapshot_payload = {
                column.name: getattr(row, column.name)
                for column in gold_model.__table__.columns
                if column.name != "source_id"
            }
            snapshot_payload.pop("extracted_at", None)
            snapshot_payload["snapshot_at"] = datetime.now()
            mysql_db.add(snapshot_model(batch_id=batch_id, source_id=row.source_id, **snapshot_payload))

    mysql_db.add(MYSQL_Gold_Snapshot_Batch(id=batch_id, status="snapshotted", source_counts=counts))
    mysql_db.commit()
    return {"batch_id": batch_id, "counts": counts}


def load_dimensions_from_snapshot(mysql_db: Session, pg_db: Session, batch_id: str) -> dict:
    synced = {"departments": 0, "courses": 0}

    departments = mysql_db.query(MYSQL_Gold_Snapshot_Departments).filter(MYSQL_Gold_Snapshot_Departments.batch_id == batch_id).all()
    for row in departments:
        pg_id = uuid5(NAMESPACE_DNS, row.source_id)
        existing = pg_db.query(PG_Departments).filter(PG_Departments.id == pg_id).first()
        if existing:
            existing.name = row.name
            existing.hod_id = None
            existing.hod_name = row.hod_name
        else:
            pg_db.add(PG_Departments(id=pg_id, name=row.name, hod_id=None, hod_name=row.hod_name))
        synced["departments"] += 1

    courses = mysql_db.query(MYSQL_Gold_Snapshot_Courses).filter(MYSQL_Gold_Snapshot_Courses.batch_id == batch_id).all()
    for row in courses:
        pg_id = uuid5(NAMESPACE_DNS, row.source_id)
        existing = pg_db.query(PG_Courses).filter(PG_Courses.id == pg_id).first()
        if existing:
            existing.name = row.name
            existing.domain = row.domain
            existing.hod_id = None
        else:
            pg_db.add(PG_Courses(id=pg_id, name=row.name, domain=row.domain, hod_id=None))
        synced["courses"] += 1

    pg_db.commit()
    return synced


def load_facts_from_snapshot(mysql_db: Session, pg_db: Session, batch_id: str) -> dict:
    synced = {
        "faculty": 0,
        "students": 0,
        "student_attendance": 0,
        "faculty_attendance": 0,
        "scores": 0,
        "fees": 0,
        "salary": 0,
    }

    faculty_rows = mysql_db.query(MYSQL_Gold_Snapshot_Faculty).filter(MYSQL_Gold_Snapshot_Faculty.batch_id == batch_id).all()
    for row in faculty_rows:
        pg_id = uuid5(NAMESPACE_DNS, row.source_id)
        existing = pg_db.query(PG_Faculty).filter(PG_Faculty.id == pg_id).first()
        payload = {
            "name": row.name,
            "email": row.email,
            "phone": row.phone,
            "city": row.city,
            "salary": row.salary,
            "is_lecturer": row.is_lecturer,
            "is_hod": row.is_hod,
            "is_principal": row.is_principal,
            "course_id": uuid5(NAMESPACE_DNS, row.course_id) if row.course_id else None,
            "department_id": uuid5(NAMESPACE_DNS, row.department_id) if row.department_id else None,
        }
        if existing:
            for key, value in payload.items():
                setattr(existing, key, value)
        else:
            pg_db.add(PG_Faculty(id=pg_id, **payload))
        synced["faculty"] += 1

    pg_db.flush()

    departments = mysql_db.query(MYSQL_Gold_Snapshot_Departments).filter(MYSQL_Gold_Snapshot_Departments.batch_id == batch_id).all()
    for row in departments:
        pg_id = uuid5(NAMESPACE_DNS, row.source_id)
        existing = pg_db.query(PG_Departments).filter(PG_Departments.id == pg_id).first()
        if existing:
            existing.hod_id = uuid5(NAMESPACE_DNS, row.hod_id) if row.hod_id else None

    courses = mysql_db.query(MYSQL_Gold_Snapshot_Courses).filter(MYSQL_Gold_Snapshot_Courses.batch_id == batch_id).all()
    for row in courses:
        pg_id = uuid5(NAMESPACE_DNS, row.source_id)
        existing = pg_db.query(PG_Courses).filter(PG_Courses.id == pg_id).first()
        if existing:
            existing.hod_id = uuid5(NAMESPACE_DNS, row.hod_id) if row.hod_id else None

    student_rows = mysql_db.query(MYSQL_Gold_Snapshot_Students).filter(MYSQL_Gold_Snapshot_Students.batch_id == batch_id).all()
    for row in student_rows:
        pg_id = uuid5(NAMESPACE_DNS, row.source_id)
        payload = {
            "name": row.name,
            "age": row.age,
            "email": row.email,
            "phone": row.phone,
            "city": row.city,
            "course_id": uuid5(NAMESPACE_DNS, row.course_id) if row.course_id else None,
            "lecturer_id": uuid5(NAMESPACE_DNS, row.lecturer_id) if row.lecturer_id else None,
            "year": row.year,
            "created_at": row.source_created_at,
        }
        existing = pg_db.query(PG_Students).filter(PG_Students.id == pg_id).first()
        if existing:
            for key, value in payload.items():
                setattr(existing, key, value)
        else:
            pg_db.add(PG_Students(id=pg_id, **payload))
        synced["students"] += 1

    pg_db.flush()

    student_att_rows = mysql_db.query(MYSQL_Gold_Snapshot_StudentAttendance).filter(MYSQL_Gold_Snapshot_StudentAttendance.batch_id == batch_id).all()
    for row in student_att_rows:
        record_id = uuid5(NAMESPACE_DNS, row.source_id)
        existing = pg_db.query(PGStudentAttendance).filter(PGStudentAttendance.id == record_id).first()
        payload = {
            "student_id": uuid5(NAMESPACE_DNS, row.student_id),
            "date": row.date,
            "is_present": row.is_present,
        }
        if existing:
            for key, value in payload.items():
                setattr(existing, key, value)
        else:
            pg_db.add(PGStudentAttendance(id=record_id, **payload))
        synced["student_attendance"] += 1

    faculty_att_rows = mysql_db.query(MYSQL_Gold_Snapshot_FacultyAttendance).filter(MYSQL_Gold_Snapshot_FacultyAttendance.batch_id == batch_id).all()
    for row in faculty_att_rows:
        record_id = uuid5(NAMESPACE_DNS, row.source_id)
        existing = pg_db.query(PGFacultyAttendance).filter(PGFacultyAttendance.id == record_id).first()
        payload = {
            "faculty_id": uuid5(NAMESPACE_DNS, row.faculty_id),
            "date": row.date,
            "is_present": row.is_present,
        }
        if existing:
            for key, value in payload.items():
                setattr(existing, key, value)
        else:
            pg_db.add(PGFacultyAttendance(id=record_id, **payload))
        synced["faculty_attendance"] += 1

    score_rows = mysql_db.query(MYSQL_Gold_Snapshot_StudentScores).filter(MYSQL_Gold_Snapshot_StudentScores.batch_id == batch_id).all()
    for row in score_rows:
        record_id = uuid5(NAMESPACE_DNS, row.source_id)
        marks_dict = row.marks if isinstance(row.marks, dict) else json.loads(row.marks) if row.marks else {}
        payload = {
            "semester": row.semester,
            "student_id": uuid5(NAMESPACE_DNS, row.student_id),
            "lecturer_id": uuid5(NAMESPACE_DNS, row.lecturer_id),
            "avg_marks": sum(marks_dict.values()) / len(marks_dict) if marks_dict else None,
        }
        existing = pg_db.query(PGStudentScores).filter(PGStudentScores.id == record_id).first()
        if existing:
            for key, value in payload.items():
                setattr(existing, key, value)
        else:
            pg_db.add(PGStudentScores(id=record_id, **payload))
        synced["scores"] += 1

    fee_rows = mysql_db.query(MYSQL_Gold_Snapshot_Fees).filter(MYSQL_Gold_Snapshot_Fees.batch_id == batch_id).all()
    for row in fee_rows:
        record_id = uuid5(NAMESPACE_DNS, row.source_id)
        payload = {
            "student_id": uuid5(NAMESPACE_DNS, row.student_id),
            "amount": float(row.amount),
            "month": row.month,
            "year": row.year,
            "is_paid": row.is_paid,
            "paid_date": row.paid_date,
        }
        existing = pg_db.query(PG_Fees).filter(PG_Fees.id == record_id).first()
        if existing:
            for key, value in payload.items():
                setattr(existing, key, value)
        else:
            pg_db.add(PG_Fees(id=record_id, **payload))
        synced["fees"] += 1

    salary_rows = mysql_db.query(MYSQL_Gold_Snapshot_Salary).filter(MYSQL_Gold_Snapshot_Salary.batch_id == batch_id).all()
    for row in salary_rows:
        record_id = uuid5(NAMESPACE_DNS, row.source_id)
        payload = {
            "faculty_id": uuid5(NAMESPACE_DNS, row.faculty_id),
            "amount": float(row.amount),
            "month": row.month,
            "year": row.year,
            "is_paid": row.is_paid,
            "paid_date": row.paid_date,
        }
        existing = pg_db.query(PG_Salary).filter(PG_Salary.id == record_id).first()
        if existing:
            for key, value in payload.items():
                setattr(existing, key, value)
        else:
            pg_db.add(PG_Salary(id=record_id, **payload))
        synced["salary"] += 1

    pg_db.commit()
    return synced


def finalize_batch(mysql_db: Session, batch_id: str, extraction_result: dict) -> dict:
    batch = mysql_db.query(MYSQL_Gold_Snapshot_Batch).filter(MYSQL_Gold_Snapshot_Batch.id == batch_id).first()
    if not batch:
        raise ValueError(f"Snapshot batch {batch_id} not found")

    for entity_name, watermark_iso in extraction_result.get("watermarks", {}).items():
        if not watermark_iso or extraction_result.get("counts", {}).get(entity_name, 0) == 0:
            continue

        watermark = datetime.fromisoformat(watermark_iso)
        state = mysql_db.query(MYSQL_ETL_Watermark).filter(MYSQL_ETL_Watermark.entity_name == entity_name).first()
        if state:
            state.last_success_at = watermark
            state.last_batch_id = batch_id
        else:
            mysql_db.add(MYSQL_ETL_Watermark(entity_name=entity_name, last_success_at=watermark, last_batch_id=batch_id))

    for entity_name, config in ENTITY_CONFIG.items():
        mysql_db.query(config["gold_model"]).delete()

    batch.status = "loaded"
    batch.completed_at = datetime.now()
    mysql_db.commit()
    return {"batch_id": batch_id, "status": batch.status}
