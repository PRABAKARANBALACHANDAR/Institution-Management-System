from database import MYSQL_BASE
from sqlalchemy import Column,String,Date,DateTime
from datetime import datetime

class MYSQL_Announcements(MYSQL_BASE):
    __tablename__="announcements"
    id=Column(String(20),primary_key=True)
    title=Column(String(100),nullable=False)
    content=Column(String(500),nullable=False)
    deadline=Column(Date,nullable=True)
    posted_by=Column(String(50),nullable=True)
    status=Column(String(20),nullable=False,default="Active")
    created_at=Column(DateTime,default=datetime.now)
    updated_at=Column(DateTime,default=datetime.now,onupdate=datetime.now)
