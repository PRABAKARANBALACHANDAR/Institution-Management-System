from sqlalchemy.orm import Session
from schemas.queries import MYSQL_Queries
from crud.utils import generate_custom_id
from fastapi import HTTPException

def create_query(db:Session,data:dict)->MYSQL_Queries:
    new_id=generate_custom_id(db,MYSQL_Queries,"Q")
    record=MYSQL_Queries(id=new_id,**data)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def get_all_queries(db:Session):
    return db.query(MYSQL_Queries).all()

def get_queries_by_role(db:Session,role:str,role_id:str):
    return db.query(MYSQL_Queries).filter(
        MYSQL_Queries.role==role,MYSQL_Queries.role_id==role_id).all()

def answer_query(db:Session,query_id:str,answer:str,answered_by:str):
    record=db.query(MYSQL_Queries).filter(MYSQL_Queries.id==query_id).first()
    if not record:
        raise HTTPException(status_code=404,detail="Query not found")
    record.answer=answer
    record.answered_by=answered_by
    db.commit()
    db.refresh(record)
    return record
