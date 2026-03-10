from datetime import datetime,date,timedelta
import os
import sys
import logging

PROJECT_ROOT="/home/prabhu/Institution Management System"
IMS_APP_DIR=os.path.join(PROJECT_ROOT,"app")
IMS_ENV_PATH=os.path.join(PROJECT_ROOT,".env")
log_path = os.path.join(PROJECT_ROOT, "logs", "etl.log")

for _p in [PROJECT_ROOT,IMS_APP_DIR]:
    if _p not in sys.path:
        sys.path.insert(0,_p)

def log_etl(msg: str):
    from datetime import datetime, timezone, timedelta
    ist = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a") as f:
        f.write(f"[{now} IST] [IMS_DAG_ETL] {msg}\n")

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.standard.operators.empty import EmptyOperator

default_args={
    "owner":"prabhu",
    "retries":2,
    "retry_delay":timedelta(minutes=2),
}

dag=DAG(
    dag_id="ims_daily_pipeline",
    default_args=default_args,
    description="IMS: MySQL OLTP → PostgreSQL OLAP + daily analytics",
    schedule=timedelta(minutes=30),
    start_date=datetime(2026,3,6),
    catchup=False,
    tags=["ims","etl","attendance"],
)

def _get_mysql_session():
    from main import MYSQL_SessionLocal
    return MYSQL_SessionLocal()

def _get_pg_session():
    from main import PG_SessionLocal
    return PG_SessionLocal()

def _safe_close(*sessions):
    for s in sessions:
        try:
            s.close()
        except Exception:
            pass

def etl_students(**kwargs):
    from dotenv import load_dotenv
    load_dotenv(IMS_ENV_PATH)
    from schemas.student import MYSQL_Students,PG_Students
    from uuid import uuid5,NAMESPACE_DNS
    mysql_db=_get_mysql_session()
    pg_db=_get_pg_session()
    try:
        students=mysql_db.query(MYSQL_Students).all()
        for s in students:
            pg_id=uuid5(NAMESPACE_DNS,s.id)
            existing=pg_db.query(PG_Students).filter(PG_Students.id==pg_id).first()
            if existing:
                existing.name=s.name
                existing.age=getattr(s,"age",None)
                existing.email=s.email
                existing.phone=s.phone
                existing.city=s.city
                existing.year=s.year
                existing.created_at=s.created_at
            else:
                record=PG_Students(
                    id=pg_id,name=s.name,age=getattr(s,"age",None),
                    email=s.email,phone=s.phone,city=s.city,
                    course_id=None,year=s.year,
                    created_at=s.created_at
                )
                pg_db.add(record)
        pg_db.commit()
        log_etl(f"[etl_students] Synced {len(students)} students")
    finally:
        _safe_close(mysql_db,pg_db)

def etl_faculty(**kwargs):
    from dotenv import load_dotenv
    load_dotenv(IMS_ENV_PATH)
    from schemas.faculty import MYSQL_Faculty,PG_Faculty
    from uuid import uuid5,NAMESPACE_DNS
    mysql_db=_get_mysql_session()
    pg_db=_get_pg_session()
    try:
        faculty_list=mysql_db.query(MYSQL_Faculty).all()
        for f in faculty_list:
            pg_id=uuid5(NAMESPACE_DNS,f.id)
            existing=pg_db.query(PG_Faculty).filter(PG_Faculty.id==pg_id).first()
            if existing:
                existing.name=f.name
                existing.salary=f.salary
                existing.is_lecturer=f.is_lecturer
                existing.is_hod=f.is_hod
                existing.is_principal=f.is_principal
            else:
                record=PG_Faculty(
                    id=pg_id,name=f.name,email=f.email,phone=f.phone,
                    city=f.city,salary=f.salary,is_lecturer=f.is_lecturer,
                    is_hod=f.is_hod,is_principal=f.is_principal,
                    department_id=None,course_id=None
                )
                pg_db.add(record)
        pg_db.commit()
        log_etl(f"[etl_faculty] Synced {len(faculty_list)} faculty")
    finally:
        _safe_close(mysql_db,pg_db)

# ETL dim_course
def etl_courses(**kwargs):
    from dotenv import load_dotenv
    load_dotenv(IMS_ENV_PATH)
    from schemas.course import MYSQL_Courses,PG_Courses
    from uuid import uuid5,NAMESPACE_DNS
    mysql_db=_get_mysql_session()
    pg_db=_get_pg_session()
    try:
        courses=mysql_db.query(MYSQL_Courses).all()
        for c in courses:
            pg_id=uuid5(NAMESPACE_DNS,c.id)
            existing=pg_db.query(PG_Courses).filter(PG_Courses.id==pg_id).first()
            if not existing:
                record=PG_Courses(id=pg_id,name=c.name,domain=c.domain,hod_id=None)
                pg_db.add(record)
        pg_db.commit()
        logger.info(f"[etl_courses] Synced {len(courses)} courses")
    finally:
        _safe_close(mysql_db,pg_db)

# ETL dim_department
def etl_departments(**kwargs):
    from dotenv import load_dotenv
    load_dotenv(IMS_ENV_PATH)
    from schemas.departments import MYSQL_Departments,PG_Departments
    from uuid import uuid5,NAMESPACE_DNS
    mysql_db=_get_mysql_session()
    pg_db=_get_pg_session()
    try:
        depts=mysql_db.query(MYSQL_Departments).all()
        for d in depts:
            pg_id=uuid5(NAMESPACE_DNS,d.id)
            existing=pg_db.query(PG_Departments).filter(PG_Departments.id==pg_id).first()
            if not existing:
                record=PG_Departments(id=pg_id,name=d.name,hod_name=d.hod_name)
                pg_db.add(record)
        pg_db.commit()
        log_etl(f"[etl_departments] Synced {len(depts)} departments")
    finally:
        _safe_close(mysql_db,pg_db)

# Generate daily data (Attendance)
def generate_faker_data(**kwargs):
    from dotenv import load_dotenv
    load_dotenv(IMS_ENV_PATH)
    from crud.faker_data_generator import generate_student_attendance, generate_faculty_attendance
    from schemas.student import MYSQL_Students
    from schemas.faculty import MYSQL_Faculty
    mysql_db=_get_mysql_session()
    try:
        students = mysql_db.query(MYSQL_Students).all()
        faculty = mysql_db.query(MYSQL_Faculty).all()
        stu_res = generate_student_attendance(mysql_db, students, days_back=1)
        fac_res = generate_faculty_attendance(mysql_db, faculty, days_back=1)
        log_etl(f"[generate_faker_data] Student attendance: {stu_res}, Faculty attendance: {fac_res}")
    except Exception as e:
        log_etl(f"Error generating fake attendance: {e}")
    finally:
        _safe_close(mysql_db)

# ETL fact_student_scores 
def etl_scores(**kwargs):
    from dotenv import load_dotenv
    load_dotenv(IMS_ENV_PATH)
    from schemas.scores import MYSQLStudentScores, PGStudentScores
    from uuid import uuid5, NAMESPACE_DNS
    import json
    mysql_db=_get_mysql_session()
    pg_db=_get_pg_session()
    try:
        scores = mysql_db.query(MYSQLStudentScores).all()
        for s in scores:
            pg_id = uuid5(NAMESPACE_DNS, s.id)
            student_uuid = uuid5(NAMESPACE_DNS, s.student_id)
            lecturer_uuid = uuid5(NAMESPACE_DNS, s.lecturer_id)
            existing = pg_db.query(PGStudentScores).filter(PGStudentScores.id == pg_id).first()
            if not existing:
                marks_dict = s.marks if isinstance(s.marks, dict) else json.loads(s.marks) if s.marks else {}
                avg = sum(marks_dict.values()) / len(marks_dict) if marks_dict else None
                record = PGStudentScores(
                    id=pg_id,
                    semester=s.semester,
                    student_id=student_uuid,
                    lecturer_id=lecturer_uuid,
                    avg_marks=avg
                )
                pg_db.add(record)
        pg_db.commit()
        log_etl(f"[etl_scores] Synced {len(scores)} scores")
    finally:
        _safe_close(mysql_db, pg_db)

# ETL student & faculty attendance (MySQL → PostgreSQL)
def sync_attendance(**kwargs):
    from dotenv import load_dotenv
    load_dotenv(IMS_ENV_PATH)
    from crud.attendance_etl_ops import sync_student_attendance_to_pg, sync_faculty_attendance_to_pg
    mysql_db=_get_mysql_session()
    pg_db=_get_pg_session()
    try:
        student_result=sync_student_attendance_to_pg(mysql_db, pg_db, None)
        faculty_result=sync_faculty_attendance_to_pg(mysql_db, pg_db, None)
        log_etl(f"[sync_attendance] Students: {student_result}, Faculty: {faculty_result}")
    finally:
        _safe_close(mysql_db, pg_db)

# Monthly salary generation (1st of month only)
def generate_salary(**kwargs):
    from dotenv import load_dotenv
    load_dotenv(IMS_ENV_PATH)
    from crud.salary_ops import generate_monthly_salary
    today=date.today()
    if today.day!=1:
        log_etl("[salary] Not 1st of month — skipping")
        return
    mysql_db=_get_mysql_session()
    try:
        records=generate_monthly_salary(mysql_db,today.month,today.year)
        log_etl(f"[salary] Generated {len(records)} salary records for {today.month}/{today.year}")
    finally:
        _safe_close(mysql_db)

# ETL revenue report (paid fees + paid salaries)
def etl_revenue(**kwargs):
    from dotenv import load_dotenv
    load_dotenv(IMS_ENV_PATH)
    from schemas.fees import MYSQL_Fees, PG_Fees
    from schemas.salary import MYSQL_Salary, PG_Salary
    from uuid import uuid5, NAMESPACE_DNS
    
    mysql_db = _get_mysql_session()
    pg_db = _get_pg_session()
    
    try:
        # 1. Sync Fees
        fees = mysql_db.query(MYSQL_Fees).all()
        for f in fees:
            pg_id = uuid5(NAMESPACE_DNS, f.id)
            student_pg_id = uuid5(NAMESPACE_DNS, f.student_id)
            
            existing = pg_db.query(PG_Fees).filter(PG_Fees.id == pg_id).first()
            if existing:
                existing.amount = float(f.amount)
                existing.month = f.month
                existing.year = f.year
                existing.is_paid = f.is_paid
                existing.paid_date = f.paid_date
            else:
                record = PG_Fees(
                    id=pg_id,
                    student_id=student_pg_id,
                    amount=float(f.amount),
                    month=f.month,
                    year=f.year,
                    is_paid=f.is_paid,
                    paid_date=f.paid_date
                )
                pg_db.add(record)
        
        # 2. Sync Salary
        salaries = mysql_db.query(MYSQL_Salary).all()
        for s in salaries:
            pg_id = uuid5(NAMESPACE_DNS, s.id)
            faculty_pg_id = uuid5(NAMESPACE_DNS, s.faculty_id)
            
            existing = pg_db.query(PG_Salary).filter(PG_Salary.id == pg_id).first()
            if existing:
                existing.amount = float(s.amount)
                existing.month = s.month
                existing.year = s.year
                existing.is_paid = s.is_paid
                existing.paid_date = s.paid_date
            else:
                record = PG_Salary(
                    id=pg_id,
                    faculty_id=faculty_pg_id,
                    amount=float(s.amount),
                    month=s.month,
                    year=s.year,
                    is_paid=s.is_paid,
                    paid_date=s.paid_date
                )
                pg_db.add(record)
                
        # 3. Sync to fact_revenue_report (kept for backward compatibility/reporting)
        # Only for PAID records as per original logic
        for f in [x for x in fees if x.is_paid]:
            pg_db.execute(
                __import__('sqlalchemy').text(
                    "INSERT INTO fact_revenue_report (id,transaction_type,entity_id,entity_name,"
                    "role,amount,month,year,is_paid,paid_date) "
                    "VALUES (:id,:ttype,:eid,:ename,:role,:amt,:month,:year,:paid,:pdate) "
                    "ON CONFLICT (id) DO UPDATE SET is_paid=True, paid_date=:pdate, amount=:amt"
                ),
                {"id":str(uuid5(NAMESPACE_DNS,f.id)),"ttype":"fees",
                 "eid":str(uuid5(NAMESPACE_DNS,f.student_id)),"ename":"",
                 "role":"student","amt":float(f.amount),"month":f.month,"year":f.year,
                 "paid":True,"pdate":f.paid_date}
            )
        for s in [x for x in salaries if x.is_paid]:
            pg_db.execute(
                __import__('sqlalchemy').text(
                    "INSERT INTO fact_revenue_report (id,transaction_type,entity_id,entity_name,"
                    "role,amount,month,year,is_paid,paid_date) "
                    "VALUES (:id,:ttype,:eid,:ename,:role,:amt,:month,:year,:paid,:pdate) "
                    "ON CONFLICT (id) DO UPDATE SET is_paid=True, paid_date=:pdate, amount=:amt"
                ),
                {"id":str(uuid5(NAMESPACE_DNS,s.id)),"ttype":"salary",
                 "eid":str(uuid5(NAMESPACE_DNS,s.faculty_id)),"ename":"",
                 "role":"faculty","amt":float(s.amount),"month":s.month,"year":s.year,
                 "paid":True,"pdate":s.paid_date}
            )

        pg_db.commit()
        log_etl(f"[etl_revenue] Synced {len(fees)} fees, {len(salaries)} salaries")
    finally:
        _safe_close(mysql_db,pg_db)

# Teacher performance calculation
def calc_teacher_performance(**kwargs):
    from dotenv import load_dotenv
    load_dotenv(IMS_ENV_PATH)
    from schemas.faculty import PG_Faculty
    from schemas.faculty_attendance import PGFacultyAttendance
    from schemas.scores import PGStudentScores
    from uuid import uuid4
    import datetime as dt
    today=dt.date.today()
    pg_db=_get_pg_session()
    try:
        faculty_list=pg_db.query(PG_Faculty).all()
        for f in faculty_list:
            att_records=pg_db.query(PGFacultyAttendance).filter(
                PGFacultyAttendance.faculty_id==f.id).all()
            total=len(att_records)
            present=sum(1 for a in att_records if a.is_present)
            att_pct=round((present/total*100),2) if total>0 else 0.0

            scores=pg_db.query(PGStudentScores).filter(
                PGStudentScores.lecturer_id==f.id).all()
            avg_score=round(sum(s.avg_marks for s in scores if s.avg_marks)/len(scores),2) if scores else None

            perf_score=round(0.4*att_pct+(0.6*avg_score if avg_score else 0),2)

            pg_db.execute(
                __import__('sqlalchemy').text(
                    "INSERT INTO fact_teacher_performance "
                    "(id,faculty_id,faculty_name,total_classes,attended_classes,"
                    "attendance_pct,avg_student_score,performance_score,month,year) "
                    "VALUES (:id,:fid,:fname,:total,:present,:att_pct,:avg,:perf,:month,:year) "
                    "ON CONFLICT DO NOTHING"
                ),
                {"id":str(uuid4()),"fid":str(f.id),"fname":f.name,
                 "total":total,"present":present,"att_pct":att_pct,
                 "avg":avg_score,"perf":perf_score,
                 "month":today.month,"year":today.year}
            )
        pg_db.commit()
        log_etl(f"[teacher_perf] Calculated for {len(faculty_list)} faculty")
    finally:
        _safe_close(pg_db)

# Define tasks 
start=EmptyOperator(task_id="start",dag=dag)
end=EmptyOperator(task_id="end",dag=dag)

t_students=PythonOperator(task_id="etl_students",python_callable=etl_students,dag=dag)
t_faculty=PythonOperator(task_id="etl_faculty",python_callable=etl_faculty,dag=dag)
t_courses=PythonOperator(task_id="etl_courses",python_callable=etl_courses,dag=dag)
t_depts=PythonOperator(task_id="etl_departments",python_callable=etl_departments,dag=dag)
t_gen_data=PythonOperator(task_id="gen_daily_attendance",python_callable=generate_faker_data,dag=dag)
t_scores=PythonOperator(task_id="etl_scores",python_callable=etl_scores,dag=dag)
t_sync_att=PythonOperator(task_id="sync_attendance",python_callable=sync_attendance,dag=dag)
t_salary=PythonOperator(task_id="generate_salary",python_callable=generate_salary,dag=dag)
t_revenue=PythonOperator(task_id="etl_revenue",python_callable=etl_revenue,dag=dag)
t_performance=PythonOperator(task_id="teacher_performance",python_callable=calc_teacher_performance,dag=dag)

# Task dependencies
# Parallel dim ETL first + generation tasks
start >> [t_students,t_faculty,t_courses,t_depts,t_gen_data]

# Scores mapping requires students and faculty.
[t_students,t_faculty] >> t_scores

# Attendance sync requires fake generation to run first
[t_gen_data, t_students, t_faculty] >> t_sync_att

# Salary generation depends on faculty list
t_faculty >> t_salary

# Revenue ETL after salary generated
t_salary >> t_revenue

# Performance calc after attendance sync and scores ETL
[t_sync_att, t_scores] >> t_performance

# End after everything
[t_revenue,t_performance,t_courses,t_depts] >> end
