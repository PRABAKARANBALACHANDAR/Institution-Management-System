from sqlalchemy.orm import Session
from schemas.leave_req import MYSQL_Leave_Req
from schemas.faculty import MYSQL_Faculty
from schemas.student_attendance import MYSQLStudentAttendance
from schemas.faculty_attendance import MYSQLFacultyAttendance
from crud.utils import generate_custom_id
from datetime import date
from fastapi import HTTPException

def create_leave_request(db:Session,data:dict)->MYSQL_Leave_Req:
    new_id=generate_custom_id(db,MYSQL_Leave_Req,"LR")
    record=MYSQL_Leave_Req(id=new_id,status="Pending",**data)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def get_all_leave_requests(db:Session):
    return db.query(MYSQL_Leave_Req).all()

def get_leave_requests_by_role(db:Session,role:str,role_id:str):
    return db.query(MYSQL_Leave_Req).filter(
        MYSQL_Leave_Req.role==role,
        MYSQL_Leave_Req.role_id==role_id).all()

def get_leave_request(db:Session,leave_id:str):
    return db.query(MYSQL_Leave_Req).filter(MYSQL_Leave_Req.id==leave_id).first()

def update_leave_status(db:Session,leave_id:str,status:str,approved_by:str=None)->MYSQL_Leave_Req:
    record=get_leave_request(db,leave_id)
    if not record:
        raise HTTPException(status_code=404,detail="Leave request not found")
    record.status=status
    if approved_by:
        record.approved_by=approved_by
    db.commit()
    db.refresh(record)
    return record

def escalate_leave(db:Session,leave_id:str,escalated_to:str)->MYSQL_Leave_Req:
    record=get_leave_request(db,leave_id)
    if not record:
        raise HTTPException(status_code=404,detail="Leave request not found")
    
    # Check if approver is present
    escalated_faculty = db.query(MYSQL_Faculty).filter(MYSQL_Faculty.id == escalated_to).first()
    if not escalated_faculty:
        raise HTTPException(status_code=404,detail="Escalation target not found")
    
    # Check if escalated_to person was present on the leave date
    leave_start = record.from_date
    attendance = db.query(MYSQLFacultyAttendance).filter(
        MYSQLFacultyAttendance.faculty_id == escalated_to,
        MYSQLFacultyAttendance.date == leave_start
    ).first()
    
    if attendance and not attendance.is_present:
        # If escalation target is also absent, escalate to principal
        principal = db.query(MYSQL_Faculty).filter(MYSQL_Faculty.is_principal == True).first()
        if principal:
            record.escalated_to = principal.id
            record.status = "Escalated to Principal"
        else:
            raise HTTPException(status_code=422, detail="No principal to escalate to")
    else:
        # Normal escalation
        record.escalated_to = escalated_to
        record.status = "Escalated"
    
    db.commit()
    db.refresh(record)
    return record
