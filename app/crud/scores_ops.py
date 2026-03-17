import csv
import io
import json
import random
import statistics
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from database import PG_SessionLocal
from schemas.faculty import MYSQL_Faculty
from schemas.scores import MYSQLStudentScores, PGStudentScores
from schemas.student import MYSQL_Students

DEFAULT_SCORE_SUBJECTS = [
    "math",
    "science",
]
_RESERVED_SCORE_COLUMNS = {"student_id", "semester", "lecturer_id"}


def create_score(
    db: Session,
    student_id: str,
    semester: int,
    marks: dict,
    lecturer_id: str | None = None,
) -> MYSQLStudentScores:
    score_id = f"{student_id}_Sem{semester}"
    existing = db.query(MYSQLStudentScores).filter(MYSQLStudentScores.id == score_id).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Score for student {student_id} semester {semester} exists")
    record = MYSQLStudentScores(
        id=score_id,
        semester=semester,
        student_id=student_id,
        marks=marks,
        lecturer_id=lecturer_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_student_scores(db: Session, student_id: str):
    return db.query(MYSQLStudentScores).filter(MYSQLStudentScores.student_id == student_id).all()


def update_score(db: Session, student_id: str, semester: int, marks: dict):
    score_id = f"{student_id}_Sem{semester}"
    record = db.query(MYSQLStudentScores).filter(MYSQLStudentScores.id == score_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Score not found")
    record.marks = marks
    db.commit()
    db.refresh(record)
    return record


def calculate_avg_marks(db_mysql: Session, student_id: str, semester: int):
    try:
        scores = db_mysql.query(MYSQLStudentScores).filter(
            MYSQLStudentScores.student_id == student_id,
            MYSQLStudentScores.semester == semester,
        ).all()

        if not scores:
            return

        all_marks = []
        for score in scores:
            marks = _normalize_marks(score.marks)
            if marks:
                all_marks.extend(marks.values())

        if not all_marks:
            avg_marks = 0.0
        else:
            avg_marks = statistics.mean([float(m) for m in all_marks if isinstance(m, (int, float))])

        db_pg = PG_SessionLocal()
        try:
            import uuid

            student_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, student_id)
            lecturer_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, scores[0].lecturer_id or "unknown")

            pg_score = db_pg.query(PGStudentScores).filter(
                PGStudentScores.student_id == student_uuid,
                PGStudentScores.semester == semester,
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
                    avg_marks=avg_marks,
                )
                db_pg.add(new_pg_score)
                db_pg.commit()
        finally:
            db_pg.close()
    except Exception as e:
        print(f"Error calculating avg marks: {e}")


def _parse_mark(value: Any):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return value

    text = str(value).strip()
    if not text:
        return None

    number = float(text)
    return int(number) if number.is_integer() else number


def _normalize_marks(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return {}
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _infer_subject_columns_from_existing_scores(db: Session) -> list[str]:
    subject_sets: dict[tuple[str, ...], int] = {}
    for record in db.query(MYSQLStudentScores.marks).all():
        marks = _normalize_marks(record.marks)
        if not marks:
            continue
        key = tuple(sorted(marks.keys()))
        subject_sets[key] = subject_sets.get(key, 0) + 1

    if not subject_sets:
        return DEFAULT_SCORE_SUBJECTS

    most_common_subjects = max(subject_sets.items(), key=lambda item: item[1])[0]
    return list(most_common_subjects)


def import_scores_from_csv(
    db: Session,
    csv_content: str,
    lecturer_id: str | None = None,
    default_semester: int | None = None,
) -> dict[str, Any]:
    reader = csv.DictReader(io.StringIO(csv_content))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV file is empty.")

    headers = [header.strip() for header in reader.fieldnames if header and header.strip()]
    if "student_id" not in headers:
        raise HTTPException(status_code=400, detail="CSV must contain a student_id column.")

    subject_columns = [column for column in headers if column not in _RESERVED_SCORE_COLUMNS]
    if not subject_columns:
        raise HTTPException(
            status_code=400,
            detail="CSV must contain at least one subject column besides student_id/semester.",
        )

    students = db.query(MYSQL_Students).all()
    student_map = {student.id: student for student in students}
    faculty_ids = {faculty_id for (faculty_id,) in db.query(MYSQL_Faculty.id).all()}
    existing_pairs = {
        (record.student_id, record.semester)
        for record in db.query(MYSQLStudentScores.student_id, MYSQLStudentScores.semester).all()
    }

    created_pairs: list[tuple[str, int]] = []
    created = 0
    skipped = 0
    failed = 0
    errors: list[str] = []

    for row_number, row in enumerate(reader, start=2):
        student_id = (row.get("student_id") or "").strip()
        semester_value = (row.get("semester") or "").strip()

        if not student_id:
            failed += 1
            errors.append(f"Row {row_number}: student_id is required.")
            continue

        semester_text = semester_value or (str(default_semester) if default_semester is not None else "")
        if not semester_text:
            failed += 1
            errors.append(f"Row {row_number}: semester is required.")
            continue

        try:
            semester = int(semester_text)
        except ValueError:
            failed += 1
            errors.append(f"Row {row_number}: invalid semester '{semester_text}'.")
            continue

        student = student_map.get(student_id)
        if student is None:
            failed += 1
            errors.append(f"Row {row_number}: unknown student_id '{student_id}'.")
            continue

        if (student_id, semester) in existing_pairs:
            skipped += 1
            continue

        try:
            marks = {
                column: parsed
                for column in subject_columns
                if (parsed := _parse_mark(row.get(column))) is not None
            }
        except ValueError:
            failed += 1
            errors.append(f"Row {row_number}: subject marks must be numeric.")
            continue

        if not marks:
            failed += 1
            errors.append(f"Row {row_number}: no numeric marks found.")
            continue

        lecturer_candidates = [
            (row.get("lecturer_id") or "").strip(),
            lecturer_id or "",
            student.lecturer_id or "",
        ]
        record_lecturer_id = next((candidate for candidate in lecturer_candidates if candidate in faculty_ids), "")
        if not record_lecturer_id:
            failed += 1
            errors.append(f"Row {row_number}: lecturer_id could not be resolved to a valid faculty id for student '{student_id}'.")
            continue

        db.add(
            MYSQLStudentScores(
                id=f"{student_id}_Sem{semester}",
                semester=semester,
                student_id=student_id,
                lecturer_id=record_lecturer_id,
                marks=marks,
            )
        )
        existing_pairs.add((student_id, semester))
        created_pairs.append((student_id, semester))
        created += 1

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Could not import scores: {exc}") from exc

    for student_id, semester in created_pairs:
        calculate_avg_marks(db, student_id, semester)

    return {
        "created": created,
        "skipped": skipped,
        "failed": failed,
        "processed_rows": created + skipped + failed,
        "subject_columns": subject_columns,
        "errors": errors[:20],
    }


def generate_score_csv_files(
    db: Session,
    students: list[MYSQL_Students],
    max_semester: int = 8,
    output_dir: str | None = None,
    subjects: list[str] | None = None,
) -> dict[str, Any]:
    if max_semester < 1:
        raise HTTPException(status_code=400, detail="max_semester must be at least 1.")

    output_path = Path(output_dir or Path(__file__).resolve().parents[2] / "generated" / "score_csvs")
    output_path.mkdir(parents=True, exist_ok=True)

    subject_columns = subjects or _infer_subject_columns_from_existing_scores(db)
    generated_files = []
    total_rows = 0

    for semester in range(1, max_semester + 1):
        semester_students = [
            student
            for student in students
            if semester <= max(1, min((student.year or 1) * 2, max_semester))
        ]
        if not semester_students:
            continue

        file_path = output_path / f"semester_{semester}_scores.csv"
        with file_path.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=["student_id", *subject_columns])
            writer.writeheader()
            for student in semester_students:
                row = {"student_id": student.id}
                for subject in subject_columns:
                    row[subject] = random.randint(40, 100)
                writer.writerow(row)

        generated_files.append(
            {
                "semester": semester,
                "file_path": str(file_path),
                "rows": len(semester_students),
            }
        )
        total_rows += len(semester_students)

    return {
        "generated_files": generated_files,
        "subjects": subject_columns,
        "rows_written": total_rows,
        "output_dir": str(output_path),
    }
