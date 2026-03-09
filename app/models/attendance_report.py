from pydantic import BaseModel
from datetime import date,datetime
from typing import Optional
from uuid import UUID

class StudentAttendanceReport(BaseModel):
    student_id:UUID
    student_name:str
    total_days:int
    present_days:int
    absent_days:int
    percentage:float
    class Config:
        from_attributes=True

class FacultyAttendanceReport(BaseModel):
    faculty_id:UUID
    faculty_name:str
    role:Optional[str]=None
    total_days:int
    present_days:int
    absent_days:int
    percentage:float
    class Config:
        from_attributes=True

class DailyAttendanceRow(BaseModel):
    student_id:str
    student_name:str
    is_present:bool
    already_marked:bool