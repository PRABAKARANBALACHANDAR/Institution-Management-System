import sys,os
_APP_DIR=os.path.dirname(os.path.abspath(__file__))
if _APP_DIR not in sys.path:
    sys.path.insert(0,_APP_DIR)

from fastapi import FastAPI,Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from exceptions.custom_errors import IMSException
from dotenv import load_dotenv

import logging
import time

os.environ['TZ'] = 'Asia/Kolkata'
if hasattr(time, 'tzset'):
    time.tzset()

class FormatterIST(logging.Formatter):
    def converter(self, timestamp):
        return time.gmtime(timestamp + 19800)

log_formatter = FormatterIST("%(asctime)s IST | %(levelname)s | %(name)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
for logger_name in ("uvicorn.error", "uvicorn.access", "fastapi"):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    
    if logger.hasHandlers():
        logger.handlers.clear()
        
    ch = logging.StreamHandler()
    ch.setFormatter(log_formatter)
    logger.addHandler(ch)
    logger.propagate = False

airflow_db_path=os.path.expanduser('~/airflow/airflow.db').replace('\\','/')
os.environ["AIRFLOW__DATABASE__SQL_ALCHEMY_CONN"]=f"sqlite:////{airflow_db_path}"

from database import (MYSQL_BASE,PG_BASE,MYSQL_Engine,PG_Engine,MYSQL_SessionLocal,PG_SessionLocal)
import schemas.analytics

MYSQL_BASE.metadata.create_all(bind=MYSQL_Engine)
PG_BASE.metadata.create_all(bind=PG_Engine)

app=FastAPI(title="Institution Management System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(IMSException)
async def ims_exception_handler(request:Request,exc:IMSException):
    return JSONResponse(status_code=exc.status_code,content={"detail":exc.detail})

@app.on_event("startup")
async def startup_event():
    try:
        from crud.permissions_ops import init_admin
        db = MYSQL_SessionLocal()
        try:
            env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
            load_dotenv(env_path)
            admin_username = os.getenv("ADMIN_USERNAME")
            admin_password = os.getenv("ADMIN_PASSWORD")
            init_admin(db, admin_username, admin_password)
        finally:
            db.close()
    except Exception as e:
        print(f"Warning: Could not initialize admin on startup: {e}")

from routers.login import router as login_router
from routers.students_route import router as students_router
from routers.faculty_route import router as faculty_router
from routers.course_route import router as course_router
from routers.department_routes import router as department_router
from routers.attendance_route import router as attendance_router
from routers.announcements_route import router as announcements_router
from routers.fees_route import router as fees_router
from routers.salary_route import router as salary_router
from routers.queries_route import router as queries_router
from routers.analytics_routes import router as analytics_router
from routers.leave_req_route import router as leave_req_router
from routers.scores_route import router as scores_router
from routers.permissions_route import router as permissions_router
from routers.seed_data_route import router as seed_data_router

app.include_router(login_router)
app.include_router(permissions_router,prefix="/permissions",tags=["Permissions"])
app.include_router(students_router)
app.include_router(faculty_router)
app.include_router(course_router)
app.include_router(department_router)
app.include_router(attendance_router,prefix="/attendance",tags=["Attendance"])
app.include_router(announcements_router,prefix="/announcements",tags=["Announcements"])
app.include_router(fees_router)
app.include_router(salary_router)
app.include_router(queries_router)
app.include_router(leave_req_router)
app.include_router(scores_router)
app.include_router(analytics_router,tags=["Analytics"])
app.include_router(seed_data_router,tags=["Seed - Test Data Generation"])
