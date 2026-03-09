from database import MYSQL_BASE
from sqlalchemy import Column,String,DateTime
from datetime import datetime

class MYSQL_Queries(MYSQL_BASE):
    __tablename__="queries"
    id=Column(String(20),primary_key=True)
    role=Column(String(50),nullable=False)
    role_id=Column(String(20),nullable=False)
    query=Column(String(500),nullable=False)
    answer=Column(String(500),nullable=True)
    answered_by=Column(String(50),nullable=True)
    created_at=Column(DateTime,default=datetime.now)
    updated_at=Column(DateTime,default=datetime.now,onupdate=datetime.now)
