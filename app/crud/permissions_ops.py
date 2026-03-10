from sqlalchemy.orm import Session
from schemas.permissions import MYSQL_Permissions,Roles
from crud.utils import generate_custom_id
from passlib.context import CryptContext
from fastapi import HTTPException

pwd_ctx=CryptContext(schemes=["bcrypt"],deprecated="auto")

PERMISSION_BOOL_FIELDS = [
    "post_principal", "post_student", "post_faculty", "post_course", "post_dept",
    "post_marks", "post_announcements", "post_leave_req", "post_queries",
    "post_fees", "post_faculty_att", "post_stud_att", "post_salary",
    "put_principal", "put_student", "put_faculty", "put_course", "put_dept",
    "put_marks", "put_announcements", "put_leave_req", "put_queries",
    "put_salary", "put_fees",
    "get_marks", "get_student", "get_faculty", "get_announcements", "get_dept",
    "get_course", "get_leave_req", "get_queries", "get_stud_att",
    "get_faculty_att", "get_salary", "get_fees", "get_analytics",
    "delete_faculty", "delete_student", "delete_course", "delete_dept",
    "delete_announcements",
]

ROLE_PERMISSIONS = {
    Roles.ADMIN: {
        # All CREATE permissions
        "post_principal": True, "post_student": True, "post_faculty": True,
        "post_course": True, "post_dept": True, "post_marks": True,
        "post_announcements": True, "post_leave_req": True, "post_queries": True,
        "post_fees": True, "post_faculty_att": True, "post_stud_att": True,
        "post_salary": True,
        # All UPDATE permissions
        "put_principal": True, "put_student": True, "put_faculty": True,
        "put_course": True, "put_dept": True, "put_marks": True,
        "put_announcements": True, "put_leave_req": True, "put_queries": True,
        "put_salary": True, "put_fees": True,
        # All READ permissions
        "get_marks": True, "get_student": True, "get_faculty": True,
        "get_announcements": True, "get_dept": True, "get_course": True,
        "get_leave_req": True, "get_queries": True, "get_stud_att": True,
        "get_faculty_att": True, "get_salary": True, "get_fees": True,
        "get_analytics": True,
        # All DELETE permissions
        "delete_faculty": True, "delete_student": True, "delete_course": True,
        "delete_dept": True, "delete_announcements": True,
    },
    Roles.PRINCIPAL: {
        # All CREATE permissions except principal
        "post_principal": False, "post_student": True, "post_faculty": True,
        "post_course": True, "post_dept": True, "post_marks": True,
        "post_announcements": True, "post_leave_req": True, "post_queries": True,
        "post_fees": True, "post_faculty_att": True, "post_stud_att": True,
        "post_salary": True,
        # All UPDATE permissions
        "put_principal": False, "put_student": True, "put_faculty": True,
        "put_course": True, "put_dept": True, "put_marks": True,
        "put_announcements": True, "put_leave_req": True, "put_queries": True,
        "put_salary": True, "put_fees": True,
        # All READ permissions
        "get_marks": True, "get_student": True, "get_faculty": True,
        "get_announcements": True, "get_dept": True, "get_course": True,
        "get_leave_req": True, "get_queries": True, "get_stud_att": True,
        "get_faculty_att": True, "get_salary": True, "get_fees": True,
        "get_analytics": True,
        # All DELETE permissions
        "delete_faculty": True, "delete_student": True, "delete_course": True,
        "delete_dept": True, "delete_announcements": True,
    },
    Roles.HOD: {
        # Limited CREATE permissions
        "post_principal": False, "post_student": False, "post_faculty": False,
        "post_course": True, "post_dept": False, "post_marks": True,
        "post_announcements": True, "post_leave_req": False, "post_queries": False,
        "post_fees": False, "post_faculty_att": True, "post_stud_att": True,
        "post_salary": False,
        # Limited UPDATE permissions
        "put_principal": False, "put_student": False, "put_faculty": False,
        "put_course": True, "put_dept": False, "put_marks": True,
        "put_announcements": True, "put_leave_req": False, "put_queries": False,
        "put_salary": False, "put_fees": False,
        # All READ permissions
        "get_marks": True, "get_student": True, "get_faculty": True,
        "get_announcements": True, "get_dept": True, "get_course": True,
        "get_leave_req": True, "get_queries": True, "get_stud_att": True,
        "get_faculty_att": True, "get_salary": True, "get_fees": True,
        "get_analytics": True,
        # Limited DELETE permissions
        "delete_faculty": False, "delete_student": False, "delete_course": False,
        "delete_dept": False, "delete_announcements": True,
    },
    Roles.FACULTY: {
        # No CREATE permissions
        "post_principal": False, "post_student": False, "post_faculty": False,
        "post_course": False, "post_dept": False, "post_marks": True,
        "post_announcements": False, "post_leave_req": True, "post_queries": True,
        "post_fees": False, "post_faculty_att": True, "post_stud_att": False,
        "post_salary": False,
        # Limited UPDATE permissions
        "put_principal": False, "put_student": False, "put_faculty": False,
        "put_course": False, "put_dept": False, "put_marks": True,
        "put_announcements": False, "put_leave_req": False, "put_queries": False,
        "put_salary": False, "put_fees": False,
        # Limited READ permissions
        "get_marks": True, "get_student": True, "get_faculty": False,
        "get_announcements": True, "get_dept": False, "get_course": True,
        "get_leave_req": True, "get_queries": True, "get_stud_att": True,
        "get_faculty_att": False, "get_salary": False, "get_fees": False,
        "get_analytics": False,
        # No DELETE permissions
        "delete_faculty": False, "delete_student": False, "delete_course": False,
        "delete_dept": False, "delete_announcements": False,
    },
    Roles.STUDENT: {
        # No CREATE permissions
        "post_principal": False, "post_student": False, "post_faculty": False,
        "post_course": False, "post_dept": False, "post_marks": False,
        "post_announcements": False, "post_leave_req": True, "post_queries": True,
        "post_fees": False, "post_faculty_att": False, "post_stud_att": False,
        "post_salary": False,
        # No UPDATE permissions
        "put_principal": False, "put_student": False, "put_faculty": False,
        "put_course": False, "put_dept": False, "put_marks": False,
        "put_announcements": False, "put_leave_req": True, "put_queries": True,
        "put_salary": False, "put_fees": False,
        # Limited READ permissions
        "get_marks": True, "get_student": True, "get_faculty": False,
        "get_announcements": True, "get_dept": False, "get_course": True,
        "get_leave_req": True, "get_queries": True, "get_stud_att": True,
        "get_faculty_att": False, "get_salary": False, "get_fees": True,
        "get_analytics": False,
        # No DELETE permissions
        "delete_faculty": False, "delete_student": False, "delete_course": False,
        "delete_dept": False, "delete_announcements": False,
    },
}

def hash_password(plain:str)->str:
    return pwd_ctx.hash(plain)

def verify_password(plain:str,hashed:str)->bool:
    return pwd_ctx.verify(plain,hashed)

def get_permissions_by_role(role: Roles) -> dict:
    return ROLE_PERMISSIONS.get(role, {field: False for field in PERMISSION_BOOL_FIELDS})

def create_permissions(db:Session,data,auto_commit:bool=True)->MYSQL_Permissions:
    existing=db.query(MYSQL_Permissions).filter(MYSQL_Permissions.username==data["username"]).first()
    if existing:
        raise HTTPException(status_code=409,detail="Username already exists")
    role=data.get("role")
    if isinstance(role,str):
        try:
            data["role"]=Roles(role.lower())
        except ValueError:
            raise HTTPException(status_code=422,detail=f"Invalid role: {role}")
    # Auto-assign permissions based on role
    role_perms = get_permissions_by_role(data["role"])
    data.update(role_perms)
    new_id=generate_custom_id(db,MYSQL_Permissions,"P")
    data["password"]=hash_password(data["password"])
    record=MYSQL_Permissions(id=new_id,**data)
    db.add(record)
    if auto_commit:
        db.commit()
        db.refresh(record)
    else:
        db.flush()
    return record

def update_permissions(db:Session,username:str,perm_data:dict)->MYSQL_Permissions:
    record=db.query(MYSQL_Permissions).filter(MYSQL_Permissions.username==username).first()
    if not record:
        raise HTTPException(status_code=404,detail="User not found")
    selected_permissions=perm_data.get("permissions",None)
    if selected_permissions is not None:
        if not isinstance(selected_permissions,dict):
            raise HTTPException(status_code=422,detail="permissions must be a key/value map")
        invalid_keys=[k for k in selected_permissions if k not in PERMISSION_BOOL_FIELDS]
        if invalid_keys:
            raise HTTPException(status_code=422,detail=f"Invalid permission keys: {', '.join(invalid_keys)}")
        for k,v in selected_permissions.items():
            setattr(record,k,bool(v))
    db.commit()
    db.refresh(record)
    return record

def init_admin(db:Session, admin_username: str, admin_password: str) -> MYSQL_Permissions:
    existing = db.query(MYSQL_Permissions).filter(MYSQL_Permissions.role == Roles.ADMIN).first()
    if existing:
        return existing
    
    admin_perms = {field: True for field in PERMISSION_BOOL_FIELDS}
    admin_perms.update({
        "username": admin_username,
        "password": admin_password,
        "role": "admin",
        "enrollment_id": None,
        "faculty_id": None,
    })
    return create_permissions(db, admin_perms, auto_commit=True)

def check_admin_exists(db:Session) -> bool:
    return db.query(MYSQL_Permissions).filter(MYSQL_Permissions.role == Roles.ADMIN).first() is not None

def check_principal_exists(db:Session) -> bool:
    from schemas.faculty import MYSQL_Faculty
    return db.query(MYSQL_Faculty).filter(MYSQL_Faculty.is_principal == True).first() is not None

def check_teacher_exists_for_course(db:Session, course_id: str, is_lecturer: bool = True) -> bool:
    from schemas.faculty import MYSQL_Faculty
    return db.query(MYSQL_Faculty).filter(
        MYSQL_Faculty.course_id == course_id,
        MYSQL_Faculty.is_lecturer == is_lecturer
    ).first() is not None
