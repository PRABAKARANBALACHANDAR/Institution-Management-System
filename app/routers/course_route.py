from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth.dependencies import RequirePermission
from crud.course_ops import create_course_db,get_all_courses_db,get_course_db,update_course_db,delete_course_db
from pydantic import BaseModel, Field
from faker import Faker
import random
fake = Faker()
from typing import Optional

router=APIRouter(tags=["Courses"])

class CourseCreate(BaseModel):
    name: str = Field(default_factory=lambda: fake.catch_phrase()[:20])
    domain: str = Field(default_factory=lambda: fake.job()[:20])
    hod_id: Optional[str] = Field(default_factory=lambda: f"F{random.randint(1000, 9999)}")

@router.post("/courses")
def create_course(course:CourseCreate,db:Session=Depends(get_db),user=Depends(RequirePermission("post_course"))):
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    return create_course_db(db,course.model_dump())

@router.get("/courses")
def get_courses(db:Session=Depends(get_db),user=Depends(RequirePermission("get_course"))):
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    return get_all_courses_db(db)

@router.get("/courses/{course_id}")
def get_course(course_id:str,db:Session=Depends(get_db),user=Depends(RequirePermission("get_course"))):
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    course=get_course_db(db,course_id)
    if not course: raise HTTPException(status_code=404,detail="Course not found")
    return course

@router.put("/courses/{course_id}")
def update_course(course_id:str,course_data:CourseCreate,db:Session=Depends(get_db),user=Depends(RequirePermission("put_course"))):
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    course=update_course_db(db,course_id,course_data.model_dump())
    if not course: raise HTTPException(status_code=404,detail="Course not found")
    return course

@router.delete("/courses/{course_id}")
def delete_course(course_id:str,db:Session=Depends(get_db),user=Depends(RequirePermission("delete_course"))):
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    if not delete_course_db(db,course_id):
        raise HTTPException(status_code=404,detail="Course not found")
    return {"detail":"Deleted successfully"}