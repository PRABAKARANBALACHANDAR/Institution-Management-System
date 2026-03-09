from sqlalchemy.orm import Session
from schemas.announcements import MYSQL_Announcements
from crud.utils import generate_custom_id
from fastapi import HTTPException

def create_announcement(db: Session, data: dict) -> MYSQL_Announcements:
    new_id = generate_custom_id(db, MYSQL_Announcements, "AN")
    record = MYSQL_Announcements(id=new_id, **data)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def get_all_announcements(db: Session):
    return db.query(MYSQL_Announcements).all()

def get_announcement(db: Session, ann_id: str):
    return db.query(MYSQL_Announcements).filter(MYSQL_Announcements.id == ann_id).first()

def update_announcement(db: Session, ann_id: str, update_data: dict):
    record = get_announcement(db, ann_id)
    if not record:
        raise HTTPException(status_code=404, detail="Announcement not found")
    for k, v in update_data.items():
        setattr(record, k, v)
    db.commit()
    db.refresh(record)
    return record

def delete_announcement(db: Session, ann_id: str) -> bool:
    record = get_announcement(db, ann_id)
    if record:
        db.delete(record)
        db.commit()
        return True
    return False
