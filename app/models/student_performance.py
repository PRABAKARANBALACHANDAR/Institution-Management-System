from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID

class StudentPerformanceResponse(BaseModel):
    student_id:UUID
    course_name:str
    marks:float
    grade:str
    created_at:datetime
    updated_at:datetime
    class Config:
        from_attributes=True