from database import MYSQL_BASE
from sqlalchemy import Column,String,Date,DateTime,ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

class MYSQL_Leave_Req(MYSQL_BASE):
    __tablename__="leave_req"
    id=Column(String(20),primary_key=True)
    role=Column(String(50),nullable=False)
    role_id=Column(String(20),nullable=False)
    leave_type=Column(String(50),nullable=False)
    from_date=Column(Date,nullable=False)
    to_date=Column(Date,nullable=False)
    reason=Column(String(100),nullable=False)
    approved_by=Column(String(20),ForeignKey("faculty.id"),nullable=True)
    escalated_to=Column(String(20),ForeignKey("faculty.id"),nullable=True)
    status=Column(String(50),nullable=False,default="Pending")
    created_at=Column(DateTime,default=datetime.now)
    updated_at=Column(DateTime,default=datetime.now,onupdate=datetime.now)
    approver=relationship("MYSQL_Faculty",foreign_keys="[MYSQL_Leave_Req.approved_by]")
    escalator=relationship("MYSQL_Faculty",foreign_keys="[MYSQL_Leave_Req.escalated_to]")
