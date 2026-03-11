"""
IMS Daily ETL Pipeline DAG
Syncs data from MySQL OLTP to PostgreSQL OLAP + generates daily analytics
"""
import os
import sys
from datetime import datetime, date, timedelta
import pendulum

# Setup project paths
PROJECT_ROOT = "/home/prabhu/Institution Management System"
IMS_APP_DIR = os.path.join(PROJECT_ROOT, "app")
IMS_ENV_PATH = os.path.join(PROJECT_ROOT, ".env")
log_path = os.path.join(PROJECT_ROOT, "logs", "etl.log")

# Add paths to sys.path for imports
for _p in [IMS_APP_DIR, PROJECT_ROOT]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Setup logging
def log_etl(msg: str):
    now = pendulum.now("Asia/Kolkata").strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a") as f:
        f.write(f"[{now} IST] [IMS_DAG_ETL] {msg}\n")

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator

from database import MYSQL_SessionLocal, PG_SessionLocal

# DAG configuration
default_args = {
    "owner": "prabhu",
    "retries": 2,
    "retry_delay": timedelta(hours=1),
}

dag = DAG(
    dag_id="ims_daily_pipeline_v2",
    default_args=default_args,
    description="IMS: MySQL OLTP → PostgreSQL OLAP + daily analytics",
    schedule="@daily",
    start_date=pendulum.datetime(2026, 3, 6, tz="Asia/Kolkata"),
    catchup=False,
    max_active_runs=1,
    tags=["ims", "etl", "attendance"],
)


def _safe_close(*sessions):
    """Close database sessions safely"""
    for s in sessions:
        try:
            s.close()
        except Exception:
            pass


def stage_golden_source(**kwargs):
    """Extract new or changed OLTP rows into transient MySQL golden tables."""
    from dotenv import load_dotenv
    load_dotenv(IMS_ENV_PATH)
    from crud.golden_source_ops import extract_incremental_to_golden

    mysql_db = MYSQL_SessionLocal()
    try:
        result = extract_incremental_to_golden(mysql_db)
        log_etl(f"[stage_golden_source] Extracted incremental golden rows: {result['counts']}")
        return result
    except Exception as e:
        log_etl(f"[stage_golden_source] Error: {e}")
        raise
    finally:
        _safe_close(mysql_db)


def create_golden_snapshot(**kwargs):
    """Persist the transient MySQL golden copy as a snapshot batch."""
    from dotenv import load_dotenv
    load_dotenv(IMS_ENV_PATH)
    from crud.golden_source_ops import create_snapshot_batch

    mysql_db = MYSQL_SessionLocal()
    try:
        result = create_snapshot_batch(mysql_db)
        log_etl(f"[create_golden_snapshot] Created batch {result['batch_id']} with counts {result['counts']}")
        return result
    except Exception as e:
        log_etl(f"[create_golden_snapshot] Error: {e}")
        raise
    finally:
        _safe_close(mysql_db)

def etl_dimensions(**kwargs):
    """Load PostgreSQL dimensions from one MySQL snapshot batch."""
    from dotenv import load_dotenv
    load_dotenv(IMS_ENV_PATH)
    from crud.golden_source_ops import load_dimensions_from_snapshot

    ti = kwargs["ti"]
    batch_info = ti.xcom_pull(task_ids="create_golden_snapshot")
    batch_id = batch_info["batch_id"]

    mysql_db = MYSQL_SessionLocal()
    pg_db = PG_SessionLocal()
    try:
        synced = load_dimensions_from_snapshot(mysql_db, pg_db, batch_id)
        log_etl(f"[etl_dimensions] Batch {batch_id}: {synced}")
    except Exception as e:
        log_etl(f"[etl_dimensions] Error: {e}")
        raise
    finally:
        _safe_close(mysql_db, pg_db)

def etl_facts(**kwargs):
    """Load PostgreSQL facts from one MySQL snapshot batch."""
    from dotenv import load_dotenv
    load_dotenv(IMS_ENV_PATH)
    from crud.golden_source_ops import load_facts_from_snapshot

    ti = kwargs["ti"]
    batch_info = ti.xcom_pull(task_ids="create_golden_snapshot")
    batch_id = batch_info["batch_id"]

    mysql_db = MYSQL_SessionLocal()
    pg_db = PG_SessionLocal()
    try:
        synced = load_facts_from_snapshot(mysql_db, pg_db, batch_id)
        log_etl(f"[etl_facts] Batch {batch_id}: {synced}")
    except Exception as e:
        log_etl(f"[etl_facts] Error: {e}")
        raise
    finally:
        _safe_close(mysql_db, pg_db)

def finalize_golden_batch(**kwargs):
    """Advance watermarks and clear transient MySQL golden tables after success."""
    from dotenv import load_dotenv
    load_dotenv(IMS_ENV_PATH)
    from crud.golden_source_ops import finalize_batch

    ti = kwargs["ti"]
    extraction_result = ti.xcom_pull(task_ids="stage_golden_source")
    batch_info = ti.xcom_pull(task_ids="create_golden_snapshot")
    batch_id = batch_info["batch_id"]

    mysql_db = MYSQL_SessionLocal()
    try:
        result = finalize_batch(mysql_db, batch_id, extraction_result)
        log_etl(f"[finalize_golden_batch] Finalized batch {result['batch_id']} with status {result['status']}")
    except Exception as e:
        log_etl(f"[finalize_golden_batch] Error: {e}")
        raise
    finally:
        _safe_close(mysql_db)

def generate_faker_data(**kwargs):
    """Generate daily fake attendance data"""
    from dotenv import load_dotenv
    load_dotenv(IMS_ENV_PATH)
    from crud.faker_data_generator import generate_student_attendance, generate_faculty_attendance
    from schemas.student import MYSQL_Students
    from schemas.faculty import MYSQL_Faculty
    
    mysql_db = MYSQL_SessionLocal()
    try:
        students = mysql_db.query(MYSQL_Students).all()
        faculty = mysql_db.query(MYSQL_Faculty).all()
        stu_res = generate_student_attendance(mysql_db, students, days_back=1)
        fac_res = generate_faculty_attendance(mysql_db, faculty, days_back=1)
        log_etl(f"[generate_faker_data] Student attendance: {stu_res}, Faculty attendance: {fac_res}")
    except Exception as e:
        log_etl(f"[generate_faker_data] Error: {e}")
        raise
    finally:
        _safe_close(mysql_db)

def generate_salary(**kwargs):
    """Generate monthly salary records (runs on 1st of month only)"""
    from dotenv import load_dotenv
    load_dotenv(IMS_ENV_PATH)
    from crud.salary_ops import generate_monthly_salary
    
    today = date.today()
    if today.day != 1:
        log_etl("[salary] Not 1st of month — skipping")
        return
    
    mysql_db = MYSQL_SessionLocal()
    try:
        records = generate_monthly_salary(mysql_db, today.month, today.year)
        log_etl(f"[salary] Generated {len(records)} salary records for {today.month}/{today.year}")
    except Exception as e:
        log_etl(f"[salary] Error: {e}")
        raise
    finally:
        _safe_close(mysql_db)

def calc_teacher_performance(**kwargs):
    """Calculate teacher performance metrics"""
    from dotenv import load_dotenv
    load_dotenv(IMS_ENV_PATH)
    from schemas.faculty import PG_Faculty
    from schemas.faculty_attendance import PGFacultyAttendance
    from schemas.scores import PGStudentScores
    from uuid import uuid4
    from sqlalchemy import text
    import datetime as dt
    
    today = dt.date.today()
    pg_db = PG_SessionLocal()
    try:
        faculty_list = pg_db.query(PG_Faculty).all()
        for f in faculty_list:
            att_records = pg_db.query(PGFacultyAttendance).filter(
                PGFacultyAttendance.faculty_id == f.id).all()
            total = len(att_records)
            present = sum(1 for a in att_records if a.is_present)
            att_pct = round((present / total * 100), 2) if total > 0 else 0.0

            scores = pg_db.query(PGStudentScores).filter(
                PGStudentScores.lecturer_id == f.id).all()
            avg_score = round(sum(s.avg_marks for s in scores if s.avg_marks) / len(scores), 2) if scores else None

            perf_score = round(0.4 * att_pct + (0.6 * avg_score if avg_score else 0), 2)

            pg_db.execute(
                text(
                    "INSERT INTO fact_teacher_performance "
                    "(id,faculty_id,faculty_name,total_classes,attended_classes,"
                    "attendance_pct,avg_student_score,performance_score,month,year) "
                    "VALUES (:id,:fid,:fname,:total,:present,:att_pct,:avg,:perf,:month,:year) "
                    "ON CONFLICT DO NOTHING"
                ),
                {"id": str(uuid4()), "fid": str(f.id), "fname": f.name,
                 "total": total, "present": present, "att_pct": att_pct,
                 "avg": avg_score, "perf": perf_score,
                 "month": today.month, "year": today.year}
            )
        pg_db.commit()
        log_etl(f"[teacher_perf] Calculated for {len(faculty_list)} faculty")
    except Exception as e:
        log_etl(f"[teacher_perf] Error: {e}")
        raise
    finally:
        _safe_close(pg_db)

# ========== DEFINE TASKS ==========

start = EmptyOperator(task_id="start", dag=dag)
end = EmptyOperator(task_id="end", dag=dag)

t_stage_golden = PythonOperator(task_id="stage_golden_source", python_callable=stage_golden_source, dag=dag)
t_snapshot = PythonOperator(task_id="create_golden_snapshot", python_callable=create_golden_snapshot, dag=dag)
t_dimensions = PythonOperator(task_id="etl_dimensions", python_callable=etl_dimensions, dag=dag)
t_facts = PythonOperator(task_id="etl_facts", python_callable=etl_facts, dag=dag)
t_gen_data = PythonOperator(task_id="gen_daily_attendance", python_callable=generate_faker_data, dag=dag)
t_salary = PythonOperator(task_id="generate_salary", python_callable=generate_salary, dag=dag)
t_performance = PythonOperator(task_id="teacher_performance", python_callable=calc_teacher_performance, dag=dag)
t_finalize = PythonOperator(task_id="finalize_golden_batch", python_callable=finalize_golden_batch, dag=dag)

# ========== TASK DEPENDENCIES ==========

# Generate fresh operational-side data first, then snapshot it into golden staging.
start >> [t_gen_data, t_salary]
[t_gen_data, t_salary] >> t_stage_golden

t_stage_golden >> t_snapshot
t_snapshot >> t_dimensions
t_dimensions >> t_facts
t_facts >> t_performance
t_performance >> t_finalize
t_finalize >> end
