from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from auth.dependencies import RequirePermission
from crud.faker_data_generator import (
    generate_departments,
    generate_courses,
    generate_faculty,
    generate_students,
    generate_student_attendance,
    generate_faculty_attendance,
    generate_student_scores,
    generate_fees_and_salaries,
    seed_all_test_data,
)
from schemas.departments import MYSQL_Departments
from schemas.course import MYSQL_Courses
from schemas.faculty import MYSQL_Faculty
from schemas.student import MYSQL_Students
from typing import Dict, Any

router = APIRouter(prefix="/seed", tags=["Seed - Test Data Generation"])


@router.post("/all")
def seed_all(
    departments: int = Query(5, description="Number of departments (default 5)"),
    courses: int = Query(10, description="Number of courses (default 10)"),
    principals: int = Query(1, description="Number of principals (default 1)"),
    hods: int = Query(5, description="Number of HODs (default 5)"),
    lecturers: int = Query(8, description="Number of lecturers (default 8)"),
    students: int = Query(50, description="Number of students (default 50)"),
    attendance_days: int = Query(30, description="Days of attendance to generate (default 30)"),
    db: Session = Depends(get_db),
    user=Depends(RequirePermission("post_principal")),
) -> Dict[str, Any]:
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    result = seed_all_test_data(
        db,
        departments_count=max(1, departments),
        courses_count=max(1, courses),
        principals_count=max(1, principals),
        hods_count=max(1, hods),
        lecturers_count=max(1, lecturers),
        students_count=max(1, students),
        attendance_days=max(1, attendance_days),
    )
    return result


@router.post("/departments")
def seed_departments(
    count: int = Query(5, description="Number of departments to create (default 5)"),
    db: Session = Depends(get_db),
    user=Depends(RequirePermission("post_principal")),
) -> Dict[str, Any]:
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    try:
        depts = generate_departments(db, count=count)
        total = db.query(MYSQL_Departments).count()
        
        return {
            "departments": [
                {"id": d.id, "name": d.name, "hod_name": d.hod_name}
                for d in depts
            ],
            "created": len(depts),
            "total": total,
            "status": "success",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/courses")
def seed_courses(
    count: int = Query(10, description="Number of courses to create (default 10)"),
    db: Session = Depends(get_db),
    user=Depends(RequirePermission("post_principal")),
) -> Dict[str, Any]:
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    try:
        depts = db.query(MYSQL_Departments).all()
        if not depts:
            raise HTTPException(
                status_code=400,
                detail="No departments found. Create departments first using /seed/departments"
            )
        
        courses = generate_courses(db, depts, count=count)
        total = db.query(MYSQL_Courses).count()
        
        return {
            "courses": [
                {"id": c.id, "name": c.name, "domain": c.domain}
                for c in courses
            ],
            "created": len(courses),
            "total": total,
            "status": "success",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/faculty")
def seed_faculty(
    principals: int = Query(1, description="Number of principals (default 1)"),
    hods: int = Query(5, description="Number of HODs (default 5)"),
    lecturers: int = Query(8, description="Number of lecturers (default 8)"),
    db: Session = Depends(get_db),
    user=Depends(RequirePermission("post_principal")),
) -> Dict[str, Any]:
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    try:
        depts = db.query(MYSQL_Departments).all()
        courses = db.query(MYSQL_Courses).all()
        
        if not depts:
            raise HTTPException(
                status_code=400,
                detail="No departments found. Create departments first using /seed/departments"
            )
        if not courses:
            raise HTTPException(
                status_code=400,
                detail="No courses found. Create courses first using /seed/courses"
            )
        
        all_fac, principal, hods = generate_faculty(
            db, depts, courses,
            principals_count=principals,
            hods_count=hods,
            lecturers_count=lecturers,
        )
        total = db.query(MYSQL_Faculty).count()
        
        return {
            "faculty": {
                "principals": [
                    {"id": f.id, "name": f.name, "is_principal": f.is_principal}
                    for f in all_fac if f.is_principal
                ],
                "hods": [
                    {"id": f.id, "name": f.name, "is_hod": f.is_hod, "department_id": f.department_id}
                    for f in all_fac if f.is_hod
                ],
                "lecturers": [
                    {"id": f.id, "name": f.name, "is_lecturer": f.is_lecturer, "course_id": f.course_id}
                    for f in all_fac if f.is_lecturer
                ],
            },
            "created": len(all_fac),
            "total": total,
            "status": "success",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/students")
def seed_students(
    count: int = Query(50, description="Number of students to create (default 50)"),
    db: Session = Depends(get_db),
    user=Depends(RequirePermission("post_principal")),
) -> Dict[str, Any]:
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    try:
        courses = db.query(MYSQL_Courses).all()
        if not courses:
            raise HTTPException(
                status_code=400,
                detail="No courses found. Create courses first using /seed/courses"
            )
        
        lecturers = db.query(MYSQL_Faculty).filter(MYSQL_Faculty.is_lecturer == True).all()
        
        students = generate_students(db, courses, lecturers, count=count)
        total = db.query(MYSQL_Students).count()
        
        return {
            "students": [
                {
                    "id": s.id,
                    "name": s.name,
                    "age": s.age,
                    "email": s.email,
                    "course_id": s.course_id,
                    "lecturer_id": s.lecturer_id,
                    "year": s.year,
                }
                for s in students
            ],
            "created": len(students),
            "total": total,
            "status": "success",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/attendance")
def seed_attendance(
    days_back: int = Query(30, description="Number of days to generate attendance (default 30)"),
    student_attendance_percentage: float = Query(0.75, description="Attendance percentage for students (0.0-1.0, default 0.75)"),
    faculty_attendance_percentage: float = Query(0.85, description="Attendance percentage for faculty (0.0-1.0, default 0.85)"),
    db: Session = Depends(get_db),
    user=Depends(RequirePermission("post_principal")),
) -> Dict[str, Any]:
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    try:
        students = db.query(MYSQL_Students).all()
        faculty = db.query(MYSQL_Faculty).all()
        
        if not students:
            raise HTTPException(
                status_code=400,
                detail="No students found. Create students first using /seed/students"
            )
        if not faculty:
            raise HTTPException(
                status_code=400,
                detail="No faculty found. Create faculty first using /seed/faculty"
            )
        
        # Validate percentages
        if not (0 <= student_attendance_percentage <= 1):
            raise HTTPException(status_code=400, detail="student_attendance_percentage must be between 0 and 1")
        if not (0 <= faculty_attendance_percentage <= 1):
            raise HTTPException(status_code=400, detail="faculty_attendance_percentage must be between 0 and 1")
        
        student_att = generate_student_attendance(
            db, students, days_back=days_back, attendance_percentage=student_attendance_percentage
        )
        faculty_att = generate_faculty_attendance(
            db, faculty, days_back=days_back, attendance_percentage=faculty_attendance_percentage
        )
        
        return {
            "attendance": {
                "students": student_att,
                "faculty": faculty_att,
            },
            "days_generated": days_back,
            "student_attendance_percentage": student_attendance_percentage,
            "faculty_attendance_percentage": faculty_attendance_percentage,
            "status": "success",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/scores")
def seed_scores(
    max_semester: int = Query(8, description="Generate score CSV files from semester 1 to this semester"),
    db: Session = Depends(get_db),
    user=Depends(RequirePermission("post_principal")),
) -> Dict[str, Any]:
    """
    Generate semester-wise score CSV files for all existing students.
    """
    try:
        students = db.query(MYSQL_Students).all()
        if not students:
            raise HTTPException(status_code=400, detail="No students found to generate score CSV files for.")
        
        result = generate_student_scores(db, students, max_semester=max_semester)
        return {
            "status": "success",
            "score_csv_files": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/financials")
def seed_financials(
    months_back: int = Query(3, description="Number of months back to generate records for"),
    db: Session = Depends(get_db),
    user=Depends(RequirePermission("post_principal")),
) -> Dict[str, Any]:
    """
    Seed fees and salaries for all existing students and faculty.
    """
    try:
        students = db.query(MYSQL_Students).all()
        faculty = db.query(MYSQL_Faculty).all()
        
        if not students or not faculty:
            raise HTTPException(status_code=400, detail="Ensure students and faculty are seeded first.")
        
        result = generate_fees_and_salaries(db, students, faculty, months_back=months_back)
        return {
            "status": "success",
            "financials": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status")
def seed_status(
    db: Session = Depends(get_db),
    user=Depends(RequirePermission("get_admin")),
) -> Dict[str, Any]:

    from schemas.student_attendance import MYSQLStudentAttendance
    from schemas.faculty_attendance import MYSQLFacultyAttendance
    
    return {
        "departments": db.query(MYSQL_Departments).count(),
        "courses": db.query(MYSQL_Courses).count(),
        "faculty": db.query(MYSQL_Faculty).count(),
        "students": db.query(MYSQL_Students).count(),
        "student_attendance_records": db.query(MYSQLStudentAttendance).count(),
        "faculty_attendance_records": db.query(MYSQLFacultyAttendance).count(),
    }
