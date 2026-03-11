from faker import Faker
from sqlalchemy.orm import Session
from schemas.departments import MYSQL_Departments
from schemas.course import MYSQL_Courses
from schemas.faculty import MYSQL_Faculty
from schemas.student import MYSQL_Students
from schemas.student_attendance import MYSQLStudentAttendance
from schemas.faculty_attendance import MYSQLFacultyAttendance
from schemas.permissions import MYSQL_Permissions
from crud.permissions_ops import create_permissions, generate_random_password
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import random
import random
import string
import json
import uuid
import calendar

fake = Faker()


def generate_student_created_at(student_year: int) -> datetime:
    now = datetime.now()
    current_academic_year = now.year if now.month >= 6 else now.year - 1
    enrollment_year = max(current_academic_year - max(student_year - 1, 0), current_academic_year - 3)
    start_window = datetime(enrollment_year, 6, 1)
    end_window = min(now, datetime(enrollment_year + 1, 5, 31, 23, 59, 59))

    if end_window <= start_window:
        return now

    random_seconds = random.randint(0, int((end_window - start_window).total_seconds()))
    return start_window + timedelta(seconds=random_seconds)

def generate_department_id() -> str:
    return f"D{random.randint(1000, 9999)}"


def generate_departments(db: Session, count: int = 5) -> List[MYSQL_Departments]:
    departments = []
    existing_depts = db.query(MYSQL_Departments).all()
    existing_dept_ids = {d.id for d in existing_depts}
    
    try:
        max_val = max([int(d.id[1:]) for d in existing_depts if d.id[1:].isdigit()])
        counter = max_val + 1
    except:
        counter = 1001
    
    department_names = [
        "Engineering", "Computer Science", "Arts & Humanities",
        "Commerce & Business", "Medical Sciences", "Law",
        "Agriculture", "Architecture", "Management", "Education"
    ]
    
    while len(departments) < count:
        dept_id = f"D{counter}"
        counter += 1
        
        if dept_id in existing_dept_ids:
            continue
        
        dept = MYSQL_Departments(
            id=dept_id,
            name=department_names[random.randint(0, len(department_names)-1)],
            hod_name=fake.name(),
        )
        db.add(dept)
        db.flush()
        departments.append(dept)
        existing_dept_ids.add(dept_id)
    
    db.commit()
    return departments


def generate_course_id() -> str:
    """Generate unique course ID: C001, C002, etc."""
    return f"C{random.randint(1000, 9999)}"


def generate_courses(db: Session, departments: List[MYSQL_Departments], count: int = 10) -> List[MYSQL_Courses]:

    courses = []
    all_courses = db.query(MYSQL_Courses).all()
    existing_course_ids = {c.id for c in all_courses}
    
    try:
        max_val = max([int(c.id[1:]) for c in all_courses if c.id[1:].isdigit()])
        counter = max_val + 1
    except:
        counter = 1001
    
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
    
    while len(courses) < count:
        course_id = f"C{counter}"
        counter += 1
        
        if course_id in existing_course_ids:
            continue
        
        course = MYSQL_Courses(
            id=course_id,
            name=course_names[random.randint(0, len(course_names)-1)],
            domain=course_domains[random.randint(0, len(course_domains)-1)],
            hod_id=None,
        )
        db.add(course)
        db.flush()
        courses.append(course)
        existing_course_ids.add(course_id)
    
    db.commit()
    return courses


def generate_faculty_id() -> str:
    """Generate unique faculty ID: F001, F002, etc."""
    return f"F{random.randint(1000, 9999)}"


def generate_faculty(
    db: Session,
    departments: List[MYSQL_Departments],
    courses: List[MYSQL_Courses],
    principals_count: int = 1,
    hods_count: int = 5,
    lecturers_count: int = 8,
) -> Tuple[List[MYSQL_Faculty], MYSQL_Faculty, List[MYSQL_Faculty]]:

    principals = []
    hods = []
    lecturers = []
    all_faculty = []
    
    # Create Principals
    current_principals = db.query(MYSQL_Faculty).filter(MYSQL_Faculty.is_principal == True).all()
    principals_to_create = max(0, principals_count - len(current_principals))
    
    # Reset counter if starting from scratch, or find max
    all_faculty_list = db.query(MYSQL_Faculty).all()
    existing_faculty_ids = {f.id for f in all_faculty_list}
    
    # Collect all existing emails and usernames to avoid duplicates
    existing_emails = {f.email for f in all_faculty_list}
    existing_emails.update({s.email for s in db.query(MYSQL_Students).all()})
    
    existing_usernames = {p.username for p in db.query(MYSQL_Permissions).all()}

    try:
        max_val = max([int(f.id[1:]) for f in all_faculty_list if f.id[1:].isdigit()])
        counter = max_val + 1
    except:
        counter = 1001

    def get_unique_email():
        while True:
            email = fake.email()
            if email not in existing_emails:
                existing_emails.add(email)
                return email

    def get_unique_username():
        while True:
            username = fake.user_name()
            if username not in existing_usernames:
                existing_usernames.add(username)
                return username
    
    for i in range(principals_to_create):
        faculty_id = f"F{counter}"
        counter += 1
        
        while faculty_id in existing_faculty_ids:
            faculty_id = f"F{counter}"
            counter += 1
            
        principal = MYSQL_Faculty(
            id=faculty_id,
            name=fake.name(),
            email=get_unique_email(),
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
        db.flush()
        principals.append(principal)
        all_faculty.append(principal)
        
        create_permissions(db, {
            "username": get_unique_username(),
            "password": generate_random_password(),
            "role": "principal",
            "faculty_id": faculty_id,
            "enrollment_id": None
        }, auto_commit=False)

    
    # Create HODs (Department Heads)
    for dept in departments:
        if len(all_faculty) - len(principals) >= hods_count: # Simplified logic to reach HOD target
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
            email=get_unique_email(),
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
        db.flush()
        hods.append(hod)
        all_faculty.append(hod)

        create_permissions(db, {
            "username": get_unique_username(),
            "password": generate_random_password(),
            "role": "hod",
            "faculty_id": faculty_id,
            "enrollment_id": None
        }, auto_commit=False)
        
        # Update department HOD
        dept.hod_id = hod.id
        dept.hod_name = hod.name
    
    # Create Lecturers
    while len(lecturers) < lecturers_count:
        faculty_id = f"F{counter}"
        counter += 1
        
        if faculty_id in existing_faculty_ids:
            continue
        
        # Assign to a random course and department
        course = random.choice(courses) if courses else None
        dept = random.choice(departments) if departments else None
        
        if not course or not dept:
            break

        lecturer = MYSQL_Faculty(
            id=faculty_id,
            name=fake.name(),
            email=get_unique_email(),
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
        db.flush()
        lecturers.append(lecturer)
        all_faculty.append(lecturer)

        create_permissions(db, {
            "username": get_unique_username(),
            "password": generate_random_password(),
            "role": "faculty",
            "faculty_id": faculty_id,
            "enrollment_id": None
        }, auto_commit=False)

    
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


def generate_student_id() -> str:
    """Generate unique student ID: S001, S002, etc."""
    return f"S{random.randint(10000, 99999)}"


def generate_students(
    db: Session,
    courses: List[MYSQL_Courses],
    lecturers: List[MYSQL_Faculty],
    count: int = 50,
) -> List[MYSQL_Students]:

    students = []
    all_students = db.query(MYSQL_Students).all()
    existing_student_ids = {s.id for s in all_students}
    
    try:
        max_val = max([int(s.id[1:]) for s in all_students if s.id[1:].isdigit()])
        counter = max_val + 1
    except:
        counter = 10001
        
    # Collect all existing emails and usernames
    existing_emails = {s.email for s in all_students}
    existing_emails.update({f.email for f in db.query(MYSQL_Faculty).all()})
    
    existing_usernames = {p.username for p in db.query(MYSQL_Permissions).all()}
    
    cities = ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Pune", "Kolkata", "Ahmedabad"]

    def get_unique_email():
        while True:
            email = fake.email()
            if email not in existing_emails:
                existing_emails.add(email)
                return email

    def get_unique_username():
        while True:
            username = fake.user_name()
            if username not in existing_usernames:
                existing_usernames.add(username)
                return username
    
    while len(students) < count:
        student_id = f"S{counter}"
        counter += 1
        
        if student_id in existing_student_ids:
            continue
        
        course = random.choice(courses)
        lecturer = random.choice(lecturers) if lecturers else None
        
        study_year = random.randint(1, 4)

        student = MYSQL_Students(
            id=student_id,
            name=fake.name(),
            age=random.randint(18, 25),
            email=get_unique_email(),
            phone=fake.numerify(text="+91##########"),
            city=random.choice(cities),
            course_id=course.id,
            lecturer_id=lecturer.id if lecturer else None,
            year=study_year,
            created_at=generate_student_created_at(study_year),
        )
        db.add(student)
        db.flush()
        students.append(student)

        create_permissions(db, {
            "username": get_unique_username(),
            "password": generate_random_password(),
            "role": "student",
            "enrollment_id": student_id,
            "faculty_id": None
        }, auto_commit=False)

    
    db.commit()
    return students

def generate_student_attendance(
    db: Session,
    students: List[MYSQL_Students],
    days_back: int = 1,
    attendance_percentage: float = 0.75,
) -> Dict[str, int]:

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
                id=f"SA{str(uuid.uuid4()).replace('-', '')[:15]}",
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
    days_back: int = 1,
    attendance_percentage: float = 0.85,
) -> Dict[str, int]:

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
                id=f"FA{str(uuid.uuid4()).replace('-', '')[:15]}",
                faculty_id=fac.id,
                date=att_date,
                is_present=is_present,
            )
            db.add(attendance)
            created += 1
    
    db.commit()
    return {"created": created, "skipped": skipped}


def generate_student_scores(
    db: Session,
    students: List[MYSQL_Students],
) -> Dict[str, int]:
    """
    Generate fake student scores.
    """
    from schemas.scores import MYSQLStudentScores
    created = 0
    # Use only students without scores
    existing = {s.student_id for s in db.query(MYSQLStudentScores).all()}
    
    for student in students:
        if student.id in existing:
            continue
        if not student.lecturer_id:
            continue
            
        score = MYSQLStudentScores(
            id=f"SC{random.randint(10000, 99999)}",
            semester=1,
            student_id=student.id,
            lecturer_id=student.lecturer_id,
            marks=json.dumps({"math": random.randint(40, 100), "science": random.randint(40, 100)})
        )
        db.add(score)
        created += 1
    
    db.commit()
    return {"created": created, "skipped": len(students) - created}

def generate_fees_and_salaries(
    db: Session,
    students: List[MYSQL_Students],
    faculty: List[MYSQL_Faculty],
    months_back: int = 3
) -> Dict[str, Dict[str, int]]:
    """Generate fake fees and salaries for the past N months and mark as paid."""
    from schemas.fees import MYSQL_Fees
    from schemas.salary import MYSQL_Salary
    
    fee_created = 0
    salary_created = 0
    today = datetime.now()
    
    for i in range(months_back):
        # Calculate target month/year
        target_date = today - timedelta(days=30 * i)
        month = target_date.month
        year = target_date.year
        
        # Generator for Students (Fees)
        existing_fees = {(f.student_id, f.month, f.year) for f in db.query(MYSQL_Fees).filter_by(month=month, year=year).all()}
        for student in students:
            if (student.id, month, year) in existing_fees:
                continue
            is_paid = random.random() < 0.9  # 90% chance they paid
            db.add(MYSQL_Fees(
                id=f"FE{str(uuid.uuid4()).replace('-', '')[:15]}",
                student_id=student.id,
                amount=random.randint(15000, 50000),
                month=month,
                year=year,
                is_paid=is_paid,
                paid_date=target_date if is_paid else None
            ))
            fee_created += 1

        # Generator for Faculty (Salary)
        existing_salary = {(s.faculty_id, s.month, s.year) for s in db.query(MYSQL_Salary).filter_by(month=month, year=year).all()}
        for fac in faculty:
            if (fac.id, month, year) in existing_salary:
                continue
            is_paid = random.random() < 0.95  # 95% paid out
            db.add(MYSQL_Salary(
                id=f"SA{str(uuid.uuid4()).replace('-', '')[:15]}",
                faculty_id=fac.id,
                amount=fac.salary if fac.salary else random.randint(40000, 150000),
                month=month,
                year=year,
                is_paid=is_paid,
                paid_date=target_date if is_paid else None
            ))
            salary_created += 1
            
    db.commit()
    return {
        "fees": {"created": fee_created},
        "salaries": {"created": salary_created}
    }

def seed_all_test_data(
    db: Session,
    departments_count: int = 5,
    courses_count: int = 10,
    principals_count: int = 1,
    hods_count: int = 5,
    lecturers_count: int = 8,
    students_count: int = 50,
    attendance_days: int = 1,
) -> Dict:
    try:
        print(" Starting Comprehensive Test Data Seeding...")
        
        # 1. Departments
        print(" Creating Departments...")
        depts = generate_departments(db, departments_count)
        dept_total = db.query(MYSQL_Departments).count()
        print(f"   ✓ Departments: {len(depts)} created, {dept_total} total")
        
        # 2. Courses
        print(" Creating Courses...")
        courses = generate_courses(db, depts, courses_count)
        course_total = db.query(MYSQL_Courses).count()
        print(f"   ✓ Courses: {len(courses)} created, {course_total} total")
        
        # 3. Faculty
        print("Creating Faculty...")
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
        print(" Creating Students...")
        lecturers = [f for f in all_fac if f.is_lecturer]
        students = generate_students(db, courses, lecturers, students_count)
        student_total = db.query(MYSQL_Students).count()
        print(f"Students: {len(students)} created, {student_total} total")
        
        # 5. Attendance
        print("Creating Attendance Records...")
        
        # Use ALL data in DB to generate attendance and scores instead of just newly generated ones
        all_db_students = db.query(MYSQL_Students).all()
        all_db_faculty = db.query(MYSQL_Faculty).all()
        
        student_att = generate_student_attendance(db, all_db_students, attendance_days)
        faculty_att = generate_faculty_attendance(db, all_db_faculty, attendance_days)
        print(f"   ✓ Student Attendance: {student_att['created']} created, {student_att['skipped']} skipped")
        print(f"   ✓ Faculty Attendance: {faculty_att['created']} created, {faculty_att['skipped']} skipped")
        
        # 6. Scores
        print("Creating Scores Records...")
        scores_res = generate_student_scores(db, all_db_students)
        print(f"   ✓ Scores: {scores_res['created']} created, {scores_res['skipped']} skipped")
        
        # 7. Fees & Salary
        print("Creating Financial Records...")
        fin_res = generate_fees_and_salaries(db, all_db_students, all_db_faculty, months_back=3)
        print(f"   ✓ Fees: {fin_res['fees']['created']} created")
        print(f"   ✓ Salaries: {fin_res['salaries']['created']} created")
        
        print("Test Data Seeding Completed Successfully!\n")
        
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
            "scores": scores_res,
            "financials": fin_res,
            "status": "success"
        }
        
    except Exception as e:
        print(f"Error during test data seeding: {str(e)}")
        db.rollback()
        return {
            "status": "error",
            "error": str(e)
        }
