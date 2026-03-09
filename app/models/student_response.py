from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class StudentResponse(BaseModel):
    id:str
    name:str
    email:Optional[str]=None
    phone:Optional[str]=None
    city:Optional[str]=None
    course_id:Optional[str]=None
    year:Optional[int]=None
    lecturer_id:Optional[str]=None
    created_at:datetime
    updated_at:datetime
    class Config:
        from_attributes=True

class StudentListResponse(BaseModel):
    id:str
    name:str
    course_id:Optional[str]=None
    year:Optional[int]=None
    class Config:
        from_attributes=True