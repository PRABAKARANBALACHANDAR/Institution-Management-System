from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID

class TeacherPerformanceResponse(BaseModel):
    faculty_id:UUID
    faculty_name:str
    department:Optional[str]=None
    course:Optional[str]=None
    total_classes:int
    attended_classes:int
    attendance_pct:float
    avg_student_score:Optional[float]=None
    performance_score:Optional[float]=None
    month:int
    year:int
    class Config:
        from_attributes=True

class TeacherPerformanceSummary(BaseModel):
    faculty_name:str
    performance_score:Optional[float]=None
    rank:Optional[int]=None