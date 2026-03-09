"""
Comprehensive Faker Data Generator for Institution Management System

Generates realistic test data for:
- Departments
- Courses
- Faculty (Lecturer, HOD, Principal roles)
- Students
- Attendance records

Respects referential integrity and role-based constraints.
"""

from faker import Faker
from sqlalchemy.orm import Session
from schemas.departments import MYSQL_Departments
from schemas.course import MYSQL_Courses
from schemas.faculty import MYSQL_Faculty
from schemas.student import MYSQL_Students
from schemas.student_attendance import MYSQLStudentAttendance
from schemas.faculty_attendance import MYSQLFacultyAttendance
from schemas.permissions import MYSQL_Permissions
from crud.permissions_ops import create_permissions
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import random
import string

fake = Faker()

# ============================================================================
# DEPARTMENT GENERATION
# ============================================================================

def generate_department_id() -> str:
    """Generate unique department ID: D001, D002, etc."""
    return f"D{random.randint(1000, 9999)}"


def generate_departments(db: Session, count: int = 5) -> List[MYSQL_Departments]:
    """
    Generate fake departments.
    
    Args:
        db: Database session
        count: Number of departments to create (default 5)
    
    Returns:
        List of created department objects
        
    Example: ["D1001", "D1002", "D1003", ...]
    """
    departments = []
    existing_dept_ids = {d.id for d in db.query(MYSQL_Departments).all()}
    
    department_names = [
        "Engineering", "Computer Science", "Arts & Humanities",
        "Commerce & Business", "Medical Sciences", "Law",
        "Agriculture", "Architecture", "Management", "Education"
    ]
    
    for i in range(count):
        dept_id = f"D{i+1001}"
        
        # Skip if already exists
        if dept_id in existing_dept_ids:
            departments.append(db.query(MYSQL_Departments).filter(
                MYSQL_Departments.id == dept_id
            ).first())
            continue
        
        dept = MYSQL_Departments(
            id=dept_id,
            name=department_names[i % len(department_names)],
            hod_name=fake.name(),  # Temporary - will be set after faculty creation
        )
        db.add(dept)
        departments.append(dept)
    
    db.commit()
    return departments


# ============================================================================
# COURSE GENERATION
# ============================================================================

def generate_course_id() -> str:
    """Generate unique course ID: C001, C002, etc."""
    return f"C{random.randint(1000, 9999)}"


def generate_courses(db: Session, departments: List[MYSQL_Departments], count: int = 10) -> List[MYSQL_Courses]:
    """
    Generate fake courses within departments.
    
    Args:
        db: Database session
        departments: List of department objects
        count: Number of courses to create (default 10)
    
    Returns:
        List of created course objects
        
    Example course IDs: ["C1001", "C1002", "C1003", ...]
    """
    courses = []
    existing_course_ids = {c.id for c in db.query(MYSQL_Courses).all()}
    
    course_names = [
        "Python Programming", "Data Science", "Web Development",
        "Cloud Computing", "Artificial Intelligence", "Database Design",
        "Machine Learning", "DevOps Engineering", "Cybersecurity",
        "Blockchain Development", "Mobile App Development", "IoT Systems"
    ]
    
    course_domains = [
        "Technology", "Finance", "Healthcare", "Engineering",
        "Business Analytics", "Artificial Intelligence"
    ]
    
    for i in range(count):
        course_id = f"C{i+1001}"
        
        # Skip if already exists
        if course_id in existing_course_ids:
            courses.append(db.query(MYSQL_Courses).filter(
                MYSQL_Courses.id == course_id
            ).first())
            continue
        
        course = MYSQL_Courses(
            id=course_id,
            name=course_names[i % len(course_names)],
            domain=course_domains[i % len(course_domains)],
            hod_id=None,  # Will be set after faculty creation
        )
        db.add(course)
        courses.append(course)
    
    db.commit()
    return courses


# ============================================================================
# FACULTY GENERATION
# ============================================================================

def generate_faculty_id() -> str:
    """Generate unique faculty ID: F001, F002, etc."""
    return f"F{random.randint(1000, 9999)}"


def generate_faculty(
    db: Session,
    departments: List[MYSQL_Departments],
    courses: List[MYSQL_Courses],
    principals_count: int = 2,
    hods_count: int = 5,
    lecturers_count: int = 8,
) -> Tuple[List[MYSQL_Faculty], MYSQL_Faculty, List[MYSQL_Faculty]]:
    """
    Generate fake faculty with different roles (Principal, HOD, Lecturer).
    
    Args:
        db: Database session
        departments: List of department objects
        courses: List of course objects
        principals_count: Number of principals (default 2)
        hods_count: Number of HODs/Department heads (default 5)
        lecturers_count: Number of lecturers (default 8)
    
    Returns:
        Tuple of (all_faculty, primary_principal, list_of_hodss)
        
    Faculty ID Format Examples:
        - Principal: F1001, F1002
        - HOD: F1003, F1004, F1005, F1006, F1007
        - Lecturer: F1008, F1009, F1010, ...
    """
    principals = []
    hods = []
    lecturers = []
    all_faculty = []
    
    existing_faculty_ids = {f.id for f in db.query(MYSQL_Faculty).all()}
    counter = 1001
    
    # Create Principals
    existing_principal = db.query(MYSQL_Faculty).filter(MYSQL_Faculty.is_principal == True).first()
    principals_to_create = 1 if not existing_principal and principals_count > 0 else 0
    
    for i in range(principals_to_create):
        faculty_id = f"F{counter}"
        counter += 1
        
        while faculty_id in existing_faculty_ids:
            faculty_id = f"F{counter}"
            counter += 1
            
        principal = MYSQL_Faculty(
            id=faculty_id,
            name=fake.name(),
            email=fake.unique.email(),
            phone=fake.numerify(text="+91##########"),
            city=fake.city(),
            is_principal=True,
            is_hod=False,
            is_lecturer=False,
            salary=random.randint(80000, 150000),
            course_id=None,
            department_id=None,
        )
        db.add(principal)
        principals.append(principal)
        all_faculty.append(principal)
    
    # Create HODs (Department Heads)
    for dept in departments:
        if len(hods) >= hods_count:
            break
            
        existing_dept_hod = db.query(MYSQL_Faculty).filter(
            MYSQL_Faculty.is_hod == True, 
            MYSQL_Faculty.department_id == dept.id
        ).first()
        
        if existing_dept_hod:
            continue

        faculty_id = f"F{counter}"
        counter += 1
        
        while faculty_id in existing_faculty_ids:
            faculty_id = f"F{counter}"
            counter += 1
        
        hod = MYSQL_Faculty(
            id=faculty_id,
            name=fake.name(),
            email=fake.unique.email(),
            phone=fake.numerify(text="+91##########"),
            city=fake.city(),
            is_principal=False,
            is_hod=True,
            is_lecturer=False,
            salary=random.randint(60000, 100000),
            course_id=None,
            department_id=dept.id,
        )
        db.add(hod)
        hods.append(hod)
        all_faculty.append(hod)
        
        # Update department HOD
        dept.hod_id = hod.id
        dept.hod_name = hod.name
    
    # Create Lecturers
    for i in range(lecturers_count):
        faculty_id = f"F{counter}"
        counter += 1
        
        if faculty_id in existing_faculty_ids:
            continue
        
        # Assign to a random course and department
        course = random.choice(courses)
        dept = random.choice(departments)
        
        lecturer = MYSQL_Faculty(
            id=faculty_id,
            name=fake.name(),
            email=fake.unique.email(),
            phone=fake.numerify(text="+91##########"),
            city=fake.city(),
            is_principal=False,
            is_hod=False,
            is_lecturer=True,
            salary=random.randint(40000, 70000),
            course_id=course.id,
            department_id=dept.id,
        )
        db.add(lecturer)
        lecturers.append(lecturer)
        all_faculty.append(lecturer)
    
    db.commit()
    
    # Update courses with HOD assignments
    available_courses = [c for c in courses if not c.hod_id]
    for hod in hods:
        if not available_courses:
            break
        assigned_course = random.choice(available_courses)
        assigned_course.hod_id = hod.id
        available_courses.remove(assigned_course)
    
    db.commit()
    
    primary_principal = principals[0] if principals else None
    return all_faculty, primary_principal, hods


# ============================================================================
# STUDENT GENERATION
# ============================================================================

def generate_student_id() -> str:
    """Generate unique student ID: S001, S002, etc."""
    return f"S{random.randint(10000, 99999)}"


def generate_students(
    db: Session,
    courses: List[MYSQL_Courses],
    lecturers: List[MYSQL_Faculty],
    count: int = 50,
) -> List[MYSQL_Students]:
    """
    Generate fake students enrolled in courses with assigned lecturers.
    
    Args:
        db: Database session
        courses: List of course objects
        lecturers: List of lecturer faculty objects
        count: Number of students to create (default 50)
    
    Returns:
        List of created student objects
        
    Student ID Format Examples:
        - "S10001", "S10002", "S10003", ...
    """
    students = []
    existing_student_ids = {s.id for s in db.query(MYSQL_Students).all()}
    counter = 10001
    
    cities = ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Pune", "Kolkata", "Ahmedabad"]
    
    for i in range(count):
        student_id = f"S{counter}"
        counter += 1
        
        if student_id in existing_student_ids:
            continue
        
        course = random.choice(courses)
        lecturer = random.choice(lecturers) if lecturers else None
        
        student = MYSQL_Students(
            id=student_id,
            name=fake.name(),
            age=random.randint(18, 25),
            email=fake.unique.email(),
            phone=fake.numerify(text="+91##########"),
            city=random.choice(cities),
            course_id=course.id,
            lecturer_id=lecturer.id if lecturer else None,
            year=random.randint(1, 4),
            created_at=datetime.now() - timedelta(days=random.randint(30, 365)),
        )
        db.add(student)
        students.append(student)
    
    db.commit()
    return students


# ============================================================================
# ATTENDANCE GENERATION
# ============================================================================

def generate_student_attendance(
    db: Session,
    students: List[MYSQL_Students],
    days_back: int = 30,
    attendance_percentage: float = 0.75,
) -> Dict[str, int]:
    """
    Generate fake student attendance records for the last N days.
    
    Args:
        db: Database session
        students: List of student objects
        days_back: Number of days to generate attendance for (default 30)
        attendance_percentage: Percentage of days marked present (default 75%)
    
    Returns:
        Dictionary with stats: {"created": count, "skipped": count}
    """
    existing_records = {
        (att.student_id, att.date)
        for att in db.query(MYSQLStudentAttendance).all()
    }
    
    created, skipped = 0, 0
    today = datetime.now().date()
    
    for student in students:
        for day_offset in range(days_back):
            att_date = today - timedelta(days=day_offset)
            
            # Skip if record already exists
            if (student.id, att_date) in existing_records:
                skipped += 1
                continue
            
            # Random attendance based on percentage
            is_present = random.random() < attendance_percentage
            
            attendance = MYSQLStudentAttendance(
                student_id=student.id,
                date=att_date,
                is_present=is_present,
            )
            db.add(attendance)
            created += 1
    
    db.commit()
    return {"created": created, "skipped": skipped}


def generate_faculty_attendance(
    db: Session,
    faculty: List[MYSQL_Faculty],
    days_back: int = 30,
    attendance_percentage: float = 0.85,
) -> Dict[str, int]:
    """
    Generate fake faculty attendance records for the last N days.
    
    Args:
        db: Database session
        faculty: List of faculty objects
        days_back: Number of days to generate attendance for (default 30)
        attendance_percentage: Percentage of days marked present (default 85%)
    
    Returns:
        Dictionary with stats: {"created": count, "skipped": count}
    """
    existing_records = {
        (att.faculty_id, att.date)
        for att in db.query(MYSQLFacultyAttendance).all()
    }
    
    created, skipped = 0, 0
    today = datetime.now().date()
    
    for fac in faculty:
        for day_offset in range(days_back):
            att_date = today - timedelta(days=day_offset)
            
            # Skip if record already exists
            if (fac.id, att_date) in existing_records:
                skipped += 1
                continue
            
            # Random attendance based on percentage (faculty usually more punctual)
            is_present = random.random() < attendance_percentage
            
            attendance = MYSQLFacultyAttendance(
                faculty_id=fac.id,
                date=att_date,
                is_present=is_present,
            )
            db.add(attendance)
            created += 1
    
    db.commit()
    return {"created": created, "skipped": skipped}


# ============================================================================
# COMPREHENSIVE SEEDING FUNCTION
# ============================================================================

def seed_all_test_data(
    db: Session,
    departments_count: int = 5,
    courses_count: int = 10,
    principals_count: int = 2,
    hods_count: int = 5,
    lecturers_count: int = 8,
    students_count: int = 50,
    attendance_days: int = 30,
) -> Dict:
    """
    Comprehensive function to seed all test data respecting referential integrity.
    
    Execution Order:
    1. Create Departments
    2. Create Courses
    3. Create Faculty (Principals, HODs, Lecturers)
    4. Create Students
    5. Create Attendance Records
    
    Args:
        db: Database session
        departments_count: Number of departments (default 5)
        courses_count: Number of courses (default 10)
        principals_count: Number of principals (default 2)
        hods_count: Number of HODs (default 5)
        lecturers_count: Number of lecturers (default 8)
        students_count: Number of students (default 50)
        attendance_days: Days of attendance to generate (default 30)
    
    Returns:
        Dictionary with statistics about created records:
        {
            "departments": {"created": int, "total": int},
            "courses": {"created": int, "total": int},
            "faculty": {
                "principals": int,
                "hods": int,
                "lecturers": int,
                "total": int
            },
            "students": {"created": int, "total": int},
            "attendance": {
                "students": {"created": int, "skipped": int},
                "faculty": {"created": int, "skipped": int}
            }
        }
    """
    try:
        print("🌱 Starting Comprehensive Test Data Seeding...")
        
        # 1. Departments
        print("📍 Creating Departments...")
        depts = generate_departments(db, departments_count)
        dept_total = db.query(MYSQL_Departments).count()
        print(f"   ✓ Departments: {len(depts)} created, {dept_total} total")
        
        # 2. Courses
        print("📚 Creating Courses...")
        courses = generate_courses(db, depts, courses_count)
        course_total = db.query(MYSQL_Courses).count()
        print(f"   ✓ Courses: {len(courses)} created, {course_total} total")
        
        # 3. Faculty
        print("👨‍🏫 Creating Faculty...")
        all_fac, principal, hods = generate_faculty(
            db, depts, courses,
            principals_count, hods_count, lecturers_count
        )
        faculty_total = db.query(MYSQL_Faculty).count()
        print(f"   ✓ Faculty: {len(all_fac)} created, {faculty_total} total")
        print(f"      - Principals: {principals_count}")
        print(f"      - HODs: {hods_count}")
        print(f"      - Lecturers: {lecturers_count}")
        
        # 4. Students
        print("🎓 Creating Students...")
        lecturers = [f for f in all_fac if f.is_lecturer]
        students = generate_students(db, courses, lecturers, students_count)
        student_total = db.query(MYSQL_Students).count()
        print(f"   ✓ Students: {len(students)} created, {student_total} total")
        
        # 5. Attendance
        print("📅 Creating Attendance Records...")
        student_att = generate_student_attendance(db, students, attendance_days)
        faculty_att = generate_faculty_attendance(db, all_fac, attendance_days)
        print(f"   ✓ Student Attendance: {student_att['created']} created, {student_att['skipped']} skipped")
        print(f"   ✓ Faculty Attendance: {faculty_att['created']} created, {faculty_att['skipped']} skipped")
        
        print("✅ Test Data Seeding Completed Successfully!\n")
        
        return {
            "departments": {
                "created": len(depts),
                "total": dept_total,
            },
            "courses": {
                "created": len(courses),
                "total": course_total,
            },
            "faculty": {
                "principals": principals_count,
                "hods": hods_count,
                "lecturers": lecturers_count,
                "total": faculty_total,
            },
            "students": {
                "created": len(students),
                "total": student_total,
            },
            "attendance": {
                "students": student_att,
                "faculty": faculty_att,
            },
            "status": "success"
        }
        
    except Exception as e:
        print(f"❌ Error during test data seeding: {str(e)}")
        db.rollback()
        return {
            "status": "error",
            "error": str(e)
        }
