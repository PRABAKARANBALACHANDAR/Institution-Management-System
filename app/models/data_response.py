from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID

class StudentResponse(BaseModel):
    id:UUID
    name:str
    age:int
    email:str
    course:str
    year:int
    created_at:datetime
    updated_at:datetime
    class Config:
        from_attributes=True

class FacultyResponse(BaseModel):
    id:UUID
    name:str
    role:Optional[str]=None
    department:Optional[str]=None
    course:Optional[str]=None
    created_at:datetime
    updated_at:datetime
    class Config:
        from_attributes=True

class CourseResponse(BaseModel):
    id:UUID
    name:str
    hod_name:Optional[str]=None
    created_at:datetime
    updated_at:datetime
    class Config:
        from_attributes=True

class DeptResponse(BaseModel):
    id:UUID
    name:str
    hod_name:Optional[str]=None
    created_at:datetime
    updated_at:datetime
    class Config:
        from_attributes=True